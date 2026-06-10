<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/maxday-icon.svg" />
    <source media="(prefers-color-scheme: light)" srcset="assets/maxday-icon-dark.svg" />
    <img src="assets/maxday-icon-dark.svg" width="96" height="96" alt="MaxDay" />
  </picture><br/>
  <strong>maxday-drama-skill</strong><br/><br/>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.8+-green.svg" alt="Python 3.8+" /></a><br/>
  <a href="README.md">简体中文</a> | <strong>English</strong> | <a href="README_TW.md">繁體中文</a> | <a href="README_JA.md">日本語</a>
</p>
<br/>

## One Command to Bring MaxDay into Your Agent Workflow

### Install via AI Agent (Recommended)

Copy and paste the following prompt directly to your AI assistant (Codex CLI / App, Claude Code, Kimi Code/Claw, MiniMax Agent, Trae, etc.), and it will automatically handle the installation and initialization for you.

**Prompt:**
> Please install maxday-drama-skill: `https://www.maxday.ai/maxday-drama-skill.zip`

### Manual Install

Run in your terminal:
```bash
npx skills add maxday-org/maxday-drama-skill
```
Requirements: Python 3.8+, no extra dependencies.
On first use, the Agent will guide you through email verification login for MaxDay.

## Let Every AI Agent Master MaxDay

Your AI Agent is already great at brainstorming, writing scripts, breaking down shots, and polishing prompts — but it still lacks an entry point into a real creation platform.

maxday-drama-skill is that entry point. Once installed, your Agent stops at "here's a suggestion" or "copy this prompt" — instead, it can directly create projects, upload scripts, manage assets, generate images and videos in batch, track task progress, and download results on MaxDay.

Before, you manually moved ideas into MaxDay. Now, the Agent executes the entire workflow for you. You just need to **give direction, confirm actions, and keep creating.**

## What It Can Do

| You want to | What Agent can do through the Skill |
|---|---|
| Make a short drama | Create project, upload script, extract characters/scenes, batch generate images & videos, download final output |
| Batch generate character art | Query model prices, loop image generation tasks, track progress, batch download results |
| Batch generate videos | Upload reference images/audio/video, loop video generation tasks, poll status, download |
| Upload script and extract assets | Upload script file, trigger AI Agent parsing, query extraction task status |
| Manage project assets | Create folders, batch upload images/videos/audio, browse resources, delete and restore |
| Quick in-project image/video generation | Create tasks in a project, batch generate, and download |
| Track generation progress | Query project, task status, locate failed tasks |
| Check costs and billing | View balance, AI cost records, transaction history, WeChat recharge |
| Manage organizations and wallets | View organizations, members, wallet summary, wallet logs, transfers |

## Use It Like This

Below are complete task examples you can send directly to your Agent after logging in to MaxDay.

### 1. Short Drama Batch Production

```
Use maxday-drama to create a short drama project called "Urban Crush"; the script is at ./script.docx.

Please help me:
1. Create a new MaxDay project, aspect ratio 9:16, style "cinematic live action";
2. Upload the script and extract all character, scene, and prop assets;
3. After extraction completes, generate a vertical hero image for each main character;
4. Then generate a 5-second opening video for the first 3 scenes;
5. When everything is done, download results to ~/Documents/dramas/urban-crush/.
```

### 2. Batch Image Generation

```
Use maxday-drama to generate 5 images.

Requirements:
- Use/create project "Neon Concept Art Project"
- Aspect ratio 9:16
- Style 1: cyberpunk neon lighting
- Style 2: soft natural realism
- Use the cheapest available model
- Prompt: Cyberpunk city on a rainy night, neon lights reflected on wet streets, cinematic composition, rich detail
```

### 3. Single Video Generation

```
Use maxday-drama to generate one video.

Requirements:
- Use/create project "Neon Short Video Project"
- Model: seedance2-pro-vvip
- Aspect ratio 9:16
- Duration: 5 seconds
- Resolution: 480p
- Prompt: Cyberpunk city on a rainy night, neon lights reflected on wet streets, slow camera push-in, cinematic lighting
```

### 4. Batch Character Art Generation

```
Use maxday-drama to generate 2 portrait images per character for the 8 characters in the current project, each in different styles.

Requirements:
- Use/create project "Neon Character Portrait Set"
- Aspect ratio 9:16
- Style 1: cyberpunk neon lighting
- Style 2: soft natural realism
- Use the cheapest available model
- Download everything to the Desktop/characters folder when done
```

### 5. Batch Video Generation

```
Use maxday-drama to batch generate videos from the 10 storyboard images in the ./storyboard/ directory.

Please help me:
1. Use/create project "Storyboard Motion Video Set";
2. Upload all images to that project's image folder;
3. Use each image as a start frame to generate a 5-second video;
4. Use the same prompt: "cinematic camera movement, dramatic lighting";
5. Batch download all completed videos to ./output/videos/.
```

### 6. Quick In-Project Image Generation

```
Use maxday-drama to quickly generate 4 concept images.

Please help me:
1. Use/create project "Concept Art Exploration Set";
2. Generate 4 concept images in that project, with these themes:
   - Cyberpunk city street, rainy night, neon reflections
   - Ancient Chinese courtyard, moonlit solitary drinking
   - Space station interior, astronaut floating in zero gravity
   - Underwater ancient city ruins, light piercing through water surface
3. Download all to Desktop when done.
```

### 7. Check Costs and Recharge

```
Use maxday-drama to check:
1. Current account balance;
2. Recent AI cost records, grouped by project;
3. If balance is below $2, create a WeChat recharge order for $10.
```

### 8. Organization Wallet Management

```
Use maxday-drama to manage my organization wallet:
1. List my organizations;
2. Check the main organization's wallet balance and recent transactions;
3. Transfer 100 credits to member alice@example.com.
```

## Safety

All operations that spend credits, delete data, create payment orders, transfer money, or trigger AI generation will be confirmed with you before execution. When you clearly express batch intent (e.g., "batch generate for me"), the Agent will execute automatically without asking for each individual step.
