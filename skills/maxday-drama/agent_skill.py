#!/usr/bin/env python3
"""
MaxDay AI production skill client.

Zero-dependency Python CLI for MaxDay AI production APIs.
Authentication uses email-code login saved in local state.
"""

import argparse
import hashlib
import json
import mimetypes
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


DEFAULT_API_BASE_URL = "https://api.bioepisode.ai/bio/dramas/v1"
DEFAULT_SITE_URL = "https://maxday.ai"
DEFAULT_STATE_PATH = "~/.maxday/state.json"
DEFAULT_OUTPUT_DIR = "/tmp/maxday"


_ssl_ctx = ssl.create_default_context()
if os.environ.get("MAXDAY_INSECURE_SSL") == "1":
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE


class MaxDaySkillError(Exception):
    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(message)


class LocalState:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(os.path.expanduser(path or os.environ.get("MAXDAY_STATE_PATH", DEFAULT_STATE_PATH)))

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def get_token(self) -> str:
        return self.load().get("access_token", "")

    def set_token(self, token: str):
        data = self.load()
        data["access_token"] = token
        self.save(data)

    def clear_token(self):
        data = self.load()
        data.pop("access_token", None)
        self.save(data)

    def get_api_base_url(self) -> str:
        return os.environ.get("MAXDAY_API_BASE_URL", "") or self.load().get("api_base_url", DEFAULT_API_BASE_URL)

    def set_api_base_url(self, api_base_url: str):
        data = self.load()
        data["api_base_url"] = api_base_url.rstrip("/")
        self.save(data)

    def get_active_project(self) -> Optional[str]:
        return self.load().get("active_project")

    def add_project(self, project_id: str, name: str = ""):
        data = self.load()
        projects = data.setdefault("projects", {})
        projects[project_id] = {
            "name": name or projects.get(project_id, {}).get("name") or project_id[:8],
            "updated_at": now_iso(),
        }
        data["active_project"] = project_id
        self.save(data)

    def switch_project(self, project_id: str) -> bool:
        data = self.load()
        projects = data.get("projects", {})
        if project_id not in projects:
            matches = [pid for pid in projects if pid.startswith(project_id)]
            if len(matches) == 1:
                project_id = matches[0]
            else:
                return False
        data["active_project"] = project_id
        self.save(data)
        return True

    def remove_project(self, project_id: str):
        data = self.load()
        data.get("projects", {}).pop(project_id, None)
        if data.get("active_project") == project_id:
            projects = data.get("projects", {})
            data["active_project"] = next(iter(projects), None)
        self.save(data)

    def upsert_chat_session(self, session_id: str, project_id: str):
        data = self.load()
        sessions = data.setdefault("chat_sessions", [])
        sessions = [item for item in sessions if item.get("id") != session_id]
        sessions.insert(0, {"id": session_id, "project_id": project_id, "updated_at": now_iso()})
        data["chat_sessions"] = sessions[:50]
        self.save(data)


class MaxDayClient:
    def __init__(self, api_base_url: str, access_token: str = "", timeout: int = 120):
        self.api_base_url = api_base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.api_base_url}{path}"

    def post(self, path: str, params: Optional[dict] = None, token_required: bool = True) -> dict:
        params = clean_params(params or {})
        if token_required:
            if not self.access_token:
                raise MaxDaySkillError("Missing MaxDay login. Run send-code, then login --save with the email code.")
            params["accessToken"] = self.access_token
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(
            self._url(path),
            data=data,
            method="POST",
            headers={
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Origin": DEFAULT_SITE_URL,
                "Referer": f"{DEFAULT_SITE_URL}/",
                "User-Agent": "MaxDaySkill/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_ctx) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            raise MaxDaySkillError(f"HTTP {exc.code}: {body}", exc.code)
        except (urllib.error.URLError, OSError, ssl.SSLError) as exc:
            raise MaxDaySkillError(f"Connection failed: {exc}")

        if isinstance(result, dict) and result.get("result", 0) != 0:
            raise MaxDaySkillError(result.get("message") or f"API returned result {result.get('result')}", result.get("result", -1))
        return result

    def send_code(self, email: str) -> dict:
        return self.post("/user/email/sendCode", {"email": email}, token_required=False)

    def login(self, email: str, email_code: str) -> dict:
        return self.post(
            "/user/login",
            {"email": email, "emailCode": email_code, "platform": "web"},
            token_required=False,
        )

    def user(self) -> dict:
        return self.post("/user/get", {})

    def balance_transfer(self, email: str, coins: int) -> dict:
        return self.post("/user/balance/transfer", {"email": email, "coins": coins})

    def project_list(self, query_flag: Optional[int] = None) -> dict:
        return self.post("/drama/project/list", {"queryFlag": query_flag})

    def project_get(self, drama_id: str, script_content_flag: int = 1) -> dict:
        return self.post("/drama/project/get", {"dramaId": drama_id, "scriptContentFlag": script_content_flag})

    def project_save(self, **params) -> dict:
        return self.post("/drama/project/save", params)

    def project_delete(self, drama_id: str) -> dict:
        return self.post("/drama/project/delete", {"dramaId": drama_id})

    def project_copy(self, drama_id: str) -> dict:
        return self.post("/drama/project/copy", {"dramaId": drama_id})

    def project_settings(self, **params) -> dict:
        return self.post("/drama/assets/analyse", params)

    def script_save(self, **params) -> dict:
        return self.post("/drama/file/script/save", params)

    def agent_task(self, drama_id: str) -> dict:
        return self.post("/drama/file/agent/task/get", {"dramaId": drama_id})

    def model_price_list(self) -> dict:
        return self.post("/common/model/price/list", {})

    def model_price_get(self, **params) -> dict:
        return self.post("/common/model/price/get", params)

    def upload_file(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise MaxDaySkillError(f"File not found: {file_path}")
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        file_name = f"{digest}{path.suffix or '.jpg'}"
        upload_info = self.post("/common/file/upload/url/get", {"fileName": file_name})
        data = upload_info.get("data") or {}
        if data.get("existFlag") == 1 and data.get("fileUrl"):
            return data["fileUrl"]
        upload_url = data.get("uploadUrl")
        file_url = data.get("fileUrl")
        if not upload_url or not file_url:
            raise MaxDaySkillError("Upload URL response is incomplete")
        content_type = data.get("contentType") or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        req = urllib.request.Request(
            upload_url,
            data=path.read_bytes(),
            method="PUT",
            headers={"Content-Type": content_type, "User-Agent": "MaxDaySkill/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_ctx):
                return file_url
        except urllib.error.HTTPError as exc:
            raise MaxDaySkillError(f"File PUT failed ({exc.code}): {exc.read().decode()}", exc.code)

    def folder_list(self, **params) -> dict:
        return self.post("/drama/file/folder/list", params)

    def folder_add(self, **params) -> dict:
        return self.post("/drama/file/folder/add", params)

    def folder_upload(self, **params) -> dict:
        return self.post("/drama/file/folder/upload", params)

    def folder_image_generate(self, **params) -> dict:
        return self.post("/drama/file/folder/image/generate", params)

    def folder_video_generate(self, **params) -> dict:
        return self.post("/drama/file/folder/video/generate", params)

    def folder_resource_get(self, resource_id: str) -> dict:
        return self.post("/drama/file/folder/resource/get", {"id": resource_id})

    def folder_resource_delete(self, ids: str) -> dict:
        return self.post("/drama/file/folder/resource/delete", {"ids": ids})

    def recycle_bin_list(self, drama_id: str) -> dict:
        return self.post("/drama/file/folder/recycleBin/list", {"dramaId": drama_id})

    def recycle_bin_restore(self, **params) -> dict:
        return self.post("/drama/file/folder/recycleBin/restore", params)

    def chat_session_create(self, drama_id: str) -> dict:
        return self.post("/chat/session/create", {"dramaId": drama_id})

    def chat_session_list(self, drama_id: str) -> dict:
        return self.post("/chat/session/list", {"dramaId": drama_id})

    def chat_message_send(self, session_id: str, user_message: str) -> dict:
        return self.post("/chat/message/send", {"sessionId": session_id, "userMessage": user_message})

    def chat_message_history(self, session_id: str) -> dict:
        return self.post("/chat/message/history", {"sessionId": session_id})

    def tools_conversation_list(self) -> dict:
        return self.post("/tools/conversation/list", {})

    def tools_conversation_save(self, name: str, description: str = "", conversation_id: str = "") -> dict:
        return self.post("/tools/conversation/save", {
            "conversationId": conversation_id,
            "name": name,
            "description": description,
        })

    def tools_asset_list(self, conversation_id: str, asset_type: Optional[int] = None) -> dict:
        return self.post("/tools/asset/list", {"conversationId": conversation_id, "type": asset_type})

    def tools_image_generate(self, **params) -> dict:
        return self.post("/tools/image/generate", params)

    def tools_video_generate(self, **params) -> dict:
        return self.post("/tools/video/generate", params)

    def costs_list(self, **params) -> dict:
        return self.post("/drama/costs/list", params)

    def costs_user(self, drama_id: str = "") -> dict:
        return self.post("/drama/costs/user", {"dramaId": drama_id})

    def pay_history(self, page_no: int, page_size: int) -> dict:
        return self.post("/pay/history/list", {"pageNo": page_no, "pageSize": page_size})

    def pay_wechat_generate(self, pay_amount_cents: int) -> dict:
        return self.post("/pay/wechat/pay/generate", {"payAmount": pay_amount_cents})

    def pay_wechat_query(self, order_no: str) -> dict:
        return self.post("/pay/wechat/order/query", {"orderNo": order_no})

    def organizations(self) -> dict:
        return self.post("/organization/my/list", {})

    def organization_create(self, **params) -> dict:
        return self.post("/organization/create", params)

    def organization_join(self, org_no: str, remark: str = "") -> dict:
        return self.post("/organization/join", {"orgNo": org_no, "remark": remark})

    def organization_members(self, org_id: str) -> dict:
        return self.post("/organization/member/list", {"orgId": org_id})

    def organization_wallet_summary(self, org_id: str) -> dict:
        return self.post("/organization/wallet/summary", {"orgId": org_id})

    def organization_wallet_logs(self, **params) -> dict:
        return self.post("/organization/wallet/logs", params)

    def organization_wallet_accounts(self, org_id: str) -> dict:
        return self.post("/organization/wallet/account/list", {"orgId": org_id})

    def organization_transfer_to_member(self, **params) -> dict:
        return self.post("/organization/wallet/transfer-to-member", params)

    def organization_return_to_wallet(self, **params) -> dict:
        return self.post("/organization/wallet/return-to-organization", params)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def clean_params(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None and v != ""}


def emit(data, as_json: bool = False):
    print(json.dumps(data, indent=2 if not as_json else None, ensure_ascii=False))


def require_yes(args, action: str):
    if not getattr(args, "yes", False):
        raise MaxDaySkillError(f"{action} requires --yes after explicit user confirmation.")


def require_generation_price_ids(args, action: str, media_type: str):
    model_id = getattr(args, "model_id", None)
    model_price_id = getattr(args, "model_price_id", None)
    if model_id is None or model_id <= 0 or model_price_id is None:
        raise MaxDaySkillError(
            f"{action} requires --model-id and --model-price-id resolved from model-prices --json. "
            f"Do not rely on --model or backend price parsing for {media_type} generation."
        )


def require_generation_cost_confirmation(args, action: str):
    estimated_price = getattr(args, "estimated_price", None)
    if estimated_price is None or estimated_price < 0:
        raise MaxDaySkillError(
            f"{action} requires --estimated-price after showing the expected charge to the user "
            "and receiving explicit confirmation."
        )


def extract_token(login_result: dict) -> str:
    data = login_result.get("data") or {}
    for key in ("accessToken", "access_token", "token"):
        if data.get(key):
            return data[key]
    return ""


def extract_project_id(result: dict) -> str:
    data = result.get("data")
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("dramaId", "id", "projectId"):
            if data.get(key):
                return str(data[key])
    return ""


def resolve_project_id(args, state: LocalState) -> str:
    project_id = getattr(args, "project_id", None) or state.get_active_project()
    if not project_id:
        raise MaxDaySkillError("Missing project id. Pass --project-id or run project-switch/project-create first.")
    return project_id


def file_url_field(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".avif"}:
        return "imageUrl"
    if ext in {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".mpeg", ".mpg"}:
        return "videoUrl"
    if ext in {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm"}:
        return "audioUrl"
    raise MaxDaySkillError(f"Unsupported media file type: {file_path}")


def add_common(parser):
    parser.add_argument("--json", action="store_true")


def build_parser():
    parser = argparse.ArgumentParser(description="MaxDay AI production skill")
    parser.add_argument("--api-base-url", default=None)
    parser.add_argument("--timeout", type=int, default=120)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("config")
    add_common(p)
    p.add_argument("--set-api-base-url")

    p = sub.add_parser("send-code")
    add_common(p)
    p.add_argument("--email", required=True)

    p = sub.add_parser("login")
    add_common(p)
    p.add_argument("--email", required=True)
    p.add_argument("--code", required=True)
    p.add_argument("--save", action="store_true")

    p = sub.add_parser("user")
    add_common(p)

    p = sub.add_parser("projects")
    add_common(p)
    p.add_argument("--query-flag", type=int)

    p = sub.add_parser("project-add")
    add_common(p)
    p.add_argument("--project-id", required=True)
    p.add_argument("--name", default="")

    p = sub.add_parser("project-switch")
    add_common(p)
    p.add_argument("--project-id", required=True)

    p = sub.add_parser("project-create")
    add_common(p)
    p.add_argument("--name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--org-id", default="0")
    p.add_argument("--use-org-wallet", action="store_true")
    p.add_argument("--members-json", default="")
    p.add_argument("--cover", default="")

    p = sub.add_parser("project-get")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--script-content-flag", type=int, default=1)

    p = sub.add_parser("project-delete")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("project-copy")
    add_common(p)
    p.add_argument("--project-id")

    p = sub.add_parser("project-settings")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--title", required=True)
    p.add_argument("--historical-background", required=True)
    p.add_argument("--visual-style", required=True)
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--duration", type=int, default=120)
    p.add_argument("--episode-count", type=int, default=1)
    p.add_argument("--language", default="Chinese")
    p.add_argument("--prompt-language", default="Chinese")
    p.add_argument("--story", default="")

    p = sub.add_parser("script-save")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--script-content", default="")
    p.add_argument("--script-file", default="")
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--language", default="VideoLanguage")
    p.add_argument("--prompt-language", default="VideoLanguage")
    p.add_argument("--extract", action="store_true")
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("agent-task")
    add_common(p)
    p.add_argument("--project-id")

    p = sub.add_parser("model-prices")
    add_common(p)

    p = sub.add_parser("model-price")
    add_common(p)
    p.add_argument("--model", required=True)
    p.add_argument("--type", type=int, required=True, choices=[1, 2, 3, 4])
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--duration", type=int)

    p = sub.add_parser("upload")
    add_common(p)
    p.add_argument("--file", required=True)

    p = sub.add_parser("folders")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--type", required=True)
    p.add_argument("--folder-id", default="")
    p.add_argument("--query-type", type=int)

    p = sub.add_parser("folder-create")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--type", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--folder-id", default="")

    p = sub.add_parser("folder-upload")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--type", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--folder-id", default="")
    p.add_argument("--source", default="skill")

    p = sub.add_parser("image-generate")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--type", default="image")
    p.add_argument("--folder-id", default="")
    p.add_argument("--name", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--model-id", type=int, required=True)
    p.add_argument("--model-price-id", type=int, required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--resolution", default="")
    p.add_argument("--ref-images", default="[]")
    p.add_argument("--source", default="skill")
    p.add_argument("--estimated-price", type=float)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("video-generate")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--type", default="video")
    p.add_argument("--folder-id", default="")
    p.add_argument("--name", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--model-id", type=int, required=True)
    p.add_argument("--model-price-id", type=int, required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--resolution", default="")
    p.add_argument("--ref-images", default="")
    p.add_argument("--ref-videos", default="")
    p.add_argument("--ref-audios", default="")
    p.add_argument("--start-image", default="")
    p.add_argument("--end-image", default="")
    p.add_argument("--source", default="skill")
    p.add_argument("--estimated-price", type=float)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("resource-get")
    add_common(p)
    p.add_argument("--resource-id", required=True)

    p = sub.add_parser("resource-delete")
    add_common(p)
    p.add_argument("--ids", required=True)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("trash")
    add_common(p)
    p.add_argument("--project-id")

    p = sub.add_parser("restore")
    add_common(p)
    p.add_argument("--project-id")
    p.add_argument("--folder-id", default="")
    p.add_argument("--resource-id", default="")

    p = sub.add_parser("chat-create")
    add_common(p)
    p.add_argument("--project-id")

    p = sub.add_parser("chat-list")
    add_common(p)
    p.add_argument("--project-id")

    p = sub.add_parser("chat-send")
    add_common(p)
    p.add_argument("--session-id", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("chat-history")
    add_common(p)
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("tools-conversations")
    add_common(p)

    p = sub.add_parser("tools-conversation-save")
    add_common(p)
    p.add_argument("--name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--conversation-id", default="")

    p = sub.add_parser("tools-assets")
    add_common(p)
    p.add_argument("--conversation-id", required=True)
    p.add_argument("--type", type=int)

    p = sub.add_parser("tools-image-generate")
    add_common(p)
    p.add_argument("--conversation-id", default="")
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", default="")
    p.add_argument("--model-id", type=int)
    p.add_argument("--model-price-id", type=int)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--resolution", default="")
    p.add_argument("--ref-images", default="")
    p.add_argument("--estimated-price", type=float)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("tools-video-generate")
    add_common(p)
    p.add_argument("--conversation-id", default="")
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", default="")
    p.add_argument("--model-id", type=int)
    p.add_argument("--model-price-id", type=int)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--aspect-ratio", default="9:16")
    p.add_argument("--resolution", default="")
    p.add_argument("--start-image", default="")
    p.add_argument("--end-image", default="")
    p.add_argument("--ref-images", default="")
    p.add_argument("--ref-videos", default="")
    p.add_argument("--ref-audios", default="")
    p.add_argument("--estimated-price", type=float)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("costs")
    add_common(p)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--project-id", default="")
    p.add_argument("--email", default="")
    p.add_argument("--model-id", type=int)

    p = sub.add_parser("costs-user")
    add_common(p)
    p.add_argument("--project-id", default="")

    p = sub.add_parser("pay-history")
    add_common(p)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)

    p = sub.add_parser("recharge-wechat")
    add_common(p)
    p.add_argument("--amount-yuan", type=float, required=True)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("pay-query")
    add_common(p)
    p.add_argument("--order-no", required=True)

    p = sub.add_parser("balance-transfer")
    add_common(p)
    p.add_argument("--email", required=True)
    p.add_argument("--coins", type=int, required=True)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("organizations")
    add_common(p)

    p = sub.add_parser("organization-create")
    add_common(p)
    p.add_argument("--name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--cover", default="")
    p.add_argument("--members-json", default="")

    p = sub.add_parser("organization-join")
    add_common(p)
    p.add_argument("--org-no", required=True)
    p.add_argument("--remark", default="")

    p = sub.add_parser("organization-members")
    add_common(p)
    p.add_argument("--org-id", required=True)

    p = sub.add_parser("organization-wallet-summary")
    add_common(p)
    p.add_argument("--org-id", required=True)

    p = sub.add_parser("organization-wallet-accounts")
    add_common(p)
    p.add_argument("--org-id", required=True)

    p = sub.add_parser("organization-wallet-logs")
    add_common(p)
    p.add_argument("--org-id", required=True)
    p.add_argument("--consume-flag", type=int, default=0)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--project-id", default="")
    p.add_argument("--model-id", type=int)
    p.add_argument("--type", default="")
    p.add_argument("--uid", default="")

    p = sub.add_parser("organization-transfer-to-member")
    add_common(p)
    p.add_argument("--org-id", required=True)
    p.add_argument("--amount", type=int, required=True)
    p.add_argument("--email", default="")
    p.add_argument("--uid", default="")
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("organization-return-to-wallet")
    add_common(p)
    p.add_argument("--org-id", required=True)
    p.add_argument("--amount", type=int, required=True)
    p.add_argument("--email", default="")
    p.add_argument("--uid", default="")
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("download")
    add_common(p)
    p.add_argument("--urls", nargs="+", required=True)
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--prefix", default="maxday")

    return parser


def download_urls(urls, output_dir: str, prefix: str) -> list:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    downloaded = []
    for url in urls:
        ext = Path(urllib.parse.urlparse(url).path).suffix or ".bin"
        digest = hashlib.sha1(url.encode()).hexdigest()[:12]
        local_path = Path(output_dir) / f"{prefix}_{digest}{ext}"
        if local_path.exists() and local_path.stat().st_size > 0:
            downloaded.append({"url": url, "local_path": str(local_path), "new": False})
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "MaxDaySkill/1.0", "Referer": DEFAULT_SITE_URL})
        try:
            with urllib.request.urlopen(req, timeout=90, context=_ssl_ctx) as resp:
                local_path.write_bytes(resp.read())
            downloaded.append({"url": url, "local_path": str(local_path), "new": True})
        except Exception as exc:
            downloaded.append({"url": url, "local_path": None, "error": str(exc), "new": False})
    return downloaded


def main():
    parser = build_parser()
    args = parser.parse_args()
    state = LocalState()
    api_base_url = (args.api_base_url or state.get_api_base_url()).rstrip("/")
    access_token = state.get_token()
    client = MaxDayClient(api_base_url=api_base_url, access_token=access_token, timeout=args.timeout)

    try:
        cmd = args.command

        if cmd == "config":
            data = state.load()
            if args.set_api_base_url:
                state.set_api_base_url(args.set_api_base_url)
                data = state.load()
            output = {
                "api_base_url": state.get_api_base_url(),
                "state_path": str(state.path),
                "has_token": bool(state.get_token()),
                "token_source": "state" if data.get("access_token") else "missing",
                "active_project": data.get("active_project"),
                "projects": data.get("projects", {}),
                "chat_sessions": data.get("chat_sessions", []),
            }

        elif cmd == "send-code":
            output = client.send_code(args.email)

        elif cmd == "login":
            output = client.login(args.email, args.code)
            token = extract_token(output)
            if args.save and token:
                state.set_token(token)
                output = {**output, "saved_token": True}

        elif cmd == "user":
            output = client.user()

        elif cmd == "projects":
            output = client.project_list(args.query_flag)
            for item in output.get("data") or []:
                pid = str(item.get("id") or item.get("dramaId") or "")
                if pid:
                    state.add_project(pid, item.get("name") or item.get("title") or "")

        elif cmd == "project-add":
            state.add_project(args.project_id, args.name)
            output = {"active_project": args.project_id}

        elif cmd == "project-switch":
            if not state.switch_project(args.project_id):
                raise MaxDaySkillError("Project is not in local state. Use project-add or projects first.")
            output = {"active_project": state.get_active_project()}

        elif cmd == "project-create":
            output = client.project_save(
                name=args.name,
                description=args.description,
                orgId=args.org_id,
                useOrgWalletFlag=1 if args.use_org_wallet else 0,
                members=args.members_json,
                cover=args.cover,
            )
            pid = extract_project_id(output)
            if pid:
                state.add_project(pid, args.name)
                output["active_project"] = pid

        elif cmd == "project-get":
            output = client.project_get(resolve_project_id(args, state), args.script_content_flag)

        elif cmd == "project-delete":
            require_yes(args, "Project deletion")
            pid = resolve_project_id(args, state)
            output = client.project_delete(pid)
            state.remove_project(pid)

        elif cmd == "project-copy":
            output = client.project_copy(resolve_project_id(args, state))

        elif cmd == "project-settings":
            output = client.project_settings(
                dramaId=resolve_project_id(args, state),
                title=args.title,
                historicalBackground=args.historical_background,
                visualStyle=args.visual_style,
                aspectRatio=args.aspect_ratio,
                duration=args.duration,
                episodeCount=args.episode_count,
                language=args.language,
                promptLanguage=args.prompt_language,
                storyPlot=args.story,
                autoFlag=0,
            )

        elif cmd == "script-save":
            if args.extract:
                require_yes(args, "Script extraction / MaxDay AI Agent run")
            if not args.script_content and not args.script_file:
                raise MaxDaySkillError("Pass --script-content or --script-file.")
            script_file_url = client.upload_file(args.script_file) if args.script_file else ""
            output = client.script_save(
                dramaId=resolve_project_id(args, state),
                aspectRatio=args.aspect_ratio,
                language=args.language,
                promptLanguage=args.prompt_language,
                scriptContent=args.script_content,
                scriptFile=script_file_url,
                autoFlag=1 if args.extract else 0,
            )
            if script_file_url:
                output["script_file_url"] = script_file_url

        elif cmd == "agent-task":
            output = client.agent_task(resolve_project_id(args, state))

        elif cmd == "model-prices":
            output = client.model_price_list()

        elif cmd == "model-price":
            output = client.model_price_get(model=args.model, type=args.type, count=args.count, duration=args.duration)

        elif cmd == "upload":
            output = {"url": client.upload_file(args.file)}

        elif cmd == "folders":
            output = client.folder_list(dramaId=resolve_project_id(args, state), type=args.type, folderId=args.folder_id, queryType=args.query_type)

        elif cmd == "folder-create":
            output = client.folder_add(dramaId=resolve_project_id(args, state), type=args.type, name=args.name, folderId=args.folder_id)

        elif cmd == "folder-upload":
            file_url = client.upload_file(args.file)
            field = file_url_field(args.file)
            output = client.folder_upload(
                dramaId=resolve_project_id(args, state),
                type=args.type,
                name=args.name or Path(args.file).name,
                folderId=args.folder_id,
                source=args.source,
                **{field: file_url},
            )
            output["file_url"] = file_url

        elif cmd == "image-generate":
            require_yes(args, "Image generation")
            require_generation_price_ids(args, "Image generation", "image")
            require_generation_cost_confirmation(args, "Image generation")
            output = client.folder_image_generate(
                dramaId=resolve_project_id(args, state),
                type=args.type,
                folderId=args.folder_id,
                name=args.name,
                prompt=args.prompt,
                modelId=args.model_id,
                modelPriceId=args.model_price_id,
                count=args.count,
                aspectRatio=args.aspect_ratio,
                resolution=args.resolution,
                refImages=args.ref_images,
                source=args.source,
                estimatedPrice=args.estimated_price,
            )

        elif cmd == "video-generate":
            require_yes(args, "Video generation")
            require_generation_price_ids(args, "Video generation", "video")
            require_generation_cost_confirmation(args, "Video generation")
            output = client.folder_video_generate(
                dramaId=resolve_project_id(args, state),
                type=args.type,
                folderId=args.folder_id,
                name=args.name,
                prompt=args.prompt,
                modelId=args.model_id,
                modelPriceId=args.model_price_id,
                count=args.count,
                duration=args.duration,
                aspectRatio=args.aspect_ratio,
                resolution=args.resolution,
                refImages=args.ref_images,
                refVideos=args.ref_videos,
                refAudios=args.ref_audios,
                startImage=args.start_image,
                endImage=args.end_image,
                source=args.source,
                estimatedPrice=args.estimated_price,
            )

        elif cmd == "resource-get":
            output = client.folder_resource_get(args.resource_id)

        elif cmd == "resource-delete":
            require_yes(args, "Resource deletion")
            output = client.folder_resource_delete(args.ids)

        elif cmd == "trash":
            output = client.recycle_bin_list(resolve_project_id(args, state))

        elif cmd == "restore":
            output = client.recycle_bin_restore(dramaId=resolve_project_id(args, state), folderId=args.folder_id, resourceId=args.resource_id)

        elif cmd == "chat-create":
            pid = resolve_project_id(args, state)
            output = client.chat_session_create(pid)
            data = output.get("data") or {}
            session_id = data.get("sessionId") or data.get("id")
            if session_id:
                state.upsert_chat_session(str(session_id), pid)

        elif cmd == "chat-list":
            output = client.chat_session_list(resolve_project_id(args, state))

        elif cmd == "chat-send":
            require_yes(args, "Chat / MaxDay AI Agent message")
            output = client.chat_message_send(args.session_id, args.message)

        elif cmd == "chat-history":
            output = client.chat_message_history(args.session_id)

        elif cmd == "tools-conversations":
            output = client.tools_conversation_list()

        elif cmd == "tools-conversation-save":
            output = client.tools_conversation_save(args.name, args.description, args.conversation_id)

        elif cmd == "tools-assets":
            output = client.tools_asset_list(args.conversation_id, args.type)

        elif cmd == "tools-image-generate":
            require_yes(args, "Standalone image generation")
            require_generation_price_ids(args, "Standalone image generation", "image")
            require_generation_cost_confirmation(args, "Standalone image generation")
            output = client.tools_image_generate(
                conversationId=args.conversation_id,
                prompt=args.prompt,
                model=args.model,
                modelId=args.model_id,
                modelPriceId=args.model_price_id,
                count=args.count,
                aspectRatio=args.aspect_ratio,
                resolution=args.resolution,
                refImages=args.ref_images,
                estimatedPrice=args.estimated_price,
            )

        elif cmd == "tools-video-generate":
            require_yes(args, "Standalone video generation")
            require_generation_price_ids(args, "Standalone video generation", "video")
            require_generation_cost_confirmation(args, "Standalone video generation")
            output = client.tools_video_generate(
                conversationId=args.conversation_id,
                prompt=args.prompt,
                model=args.model,
                modelId=args.model_id,
                modelPriceId=args.model_price_id,
                count=args.count,
                duration=args.duration,
                aspectRatio=args.aspect_ratio,
                resolution=args.resolution,
                startImage=args.start_image,
                endImage=args.end_image,
                refImages=args.ref_images,
                refVideos=args.ref_videos,
                refAudios=args.ref_audios,
                estimatedPrice=args.estimated_price,
            )

        elif cmd == "costs":
            output = client.costs_list(pageNo=args.page_no, pageSize=args.page_size, dramaId=args.project_id, email=args.email, modelId=args.model_id)

        elif cmd == "costs-user":
            output = client.costs_user(args.project_id)

        elif cmd == "pay-history":
            output = client.pay_history(args.page_no, args.page_size)

        elif cmd == "recharge-wechat":
            require_yes(args, "Recharge QR code generation")
            output = client.pay_wechat_generate(int(round(args.amount_yuan * 100)))

        elif cmd == "pay-query":
            output = client.pay_wechat_query(args.order_no)

        elif cmd == "balance-transfer":
            require_yes(args, "Balance transfer")
            output = client.balance_transfer(args.email, args.coins)

        elif cmd == "organizations":
            output = client.organizations()

        elif cmd == "organization-create":
            output = client.organization_create(name=args.name, description=args.description, cover=args.cover, members=args.members_json)

        elif cmd == "organization-join":
            output = client.organization_join(args.org_no, args.remark)

        elif cmd == "organization-members":
            output = client.organization_members(args.org_id)

        elif cmd == "organization-wallet-summary":
            output = client.organization_wallet_summary(args.org_id)

        elif cmd == "organization-wallet-accounts":
            output = client.organization_wallet_accounts(args.org_id)

        elif cmd == "organization-wallet-logs":
            output = client.organization_wallet_logs(
                orgId=args.org_id,
                consumeFlag=args.consume_flag,
                pageNo=args.page_no,
                pageSize=args.page_size,
                dramaId=args.project_id,
                modelId=args.model_id,
                type=args.type,
                uid=args.uid,
            )

        elif cmd == "organization-transfer-to-member":
            require_yes(args, "Organization wallet transfer to member")
            output = client.organization_transfer_to_member(orgId=args.org_id, amount=args.amount, email=args.email, uid=args.uid)

        elif cmd == "organization-return-to-wallet":
            require_yes(args, "Member wallet return to organization wallet")
            output = client.organization_return_to_wallet(orgId=args.org_id, amount=args.amount, email=args.email, uid=args.uid)

        elif cmd == "download":
            output = {"downloaded": download_urls(args.urls, args.output_dir, args.prefix)}

        else:
            parser.error(f"Unknown command: {cmd}")
            return

        emit(output, getattr(args, "json", False))

    except MaxDaySkillError as exc:
        emit({"error": exc.message, "code": exc.code}, True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
