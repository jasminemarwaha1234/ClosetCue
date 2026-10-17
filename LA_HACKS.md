# LA Hacks AI Hackathon 2026: context for agents

Read this before working on this repo. It covers the event's deadline, rules, tracks, sponsor challenges and schedule, plus repo facts that affect what you build.

Sources, pulled 2026-10-17 at about 1:45 PM PDT: the live site's data endpoints (`https://live.lahacks.com/api/content`, `https://live.lahacks.com/api/schedule`), the published hacker guide, the Devpost page, and each sponsor's challenge doc. Where sources disagree, this file says so. If something here matters for a decision, re-check the live source: organizers edit these during the event.

## The hard constraints

- **Hacking window:** Saturday Oct 17, 12:00 PM PDT to **Sunday Oct 18, 12:00 PM PDT**. Submission closes at noon sharp on Devpost. No code may be written after that, there is no grace period, and late submissions aren't accepted.
  - The Devpost Rules tab still says "8am (PDT), Sunday, April 26th". That text is left over from the spring LA Hacks. The hacker guide and the Devpost header both say Oct 18, 12:00 PM PDT, so that's the real deadline.
- **Team:** at most 4 members, all admitted hackers. The whole team must be present in person for judging on Sunday.
- **New work only:** all coding happens during the window. Planning beforehand is fine. Pre-existing open-source code may be used, but anything built before the event must be marked, and judges only score new work.
- **Track choice:** each project picks **exactly one** of the three main LA Hacks tracks (Model Learning, Beyond the Digital, Applied Intelligence). It may also enter the Agentverse track (Fetch.ai) and any company challenges whose requirements it meets.
- **Prize rules:** overall 1st/2nd/3rd winners don't also get a track prize. Agentverse and company challenge prizes stack on top of LA Hacks prizes.

### What the Devpost submission must include

1. **Project description:** what it does, the problem it solves, which track it's in, and how it meets each company challenge it's entered in.
2. **Public code repository** (GitHub or similar), well documented. This repo's remote is `https://github.com/jasminemarwaha1234/LaHacksAI`: confirm it's public before submitting.
3. **Demo video, 2–3 minutes:** a walkthrough of features, functionality and how it works.
4. **A complete Devpost page:** summary, technologies used, extra resources (Figma, API docs).

Plan to have the video recorded and the Devpost page drafted by about 10–11 AM Sunday. The last hour always goes to surprises.

## Judging

Judging criteria (from Devpost and the hacker guide), unweighted:

| Criterion | What judges look for |
| --- | --- |
| Technical depth | Real engineering effort and system design, beyond simple integrations or templates. |
| Product thinking & impact | A sharp, specific problem and user; a believable real-world solution. |
| Execution & polish | Working functionality, a smooth demo, a cohesive product. |
| Originality & insight | A fresh idea or framing that stands out. |

- **Round 1, Science Fair (Sun 12:30–2:00 PM, Alumni Center):** teams demo at an assigned table, announced in Discord `#announcements`. Several judges visit, about 4–5 minutes each. Practice a 60–90 second pitch plus a live demo.
- **Round 2, Top 5 Demos (Sun 2:00–3:00 PM):** top 5 across all tracks present on stage. 8 minutes per team: a 3-minute pitch/demo, then 5 minutes of judge Q&A.
- **Closing ceremony and winners:** Sun 3:00–4:00 PM, Collins Conference Room.

## Main tracks

| # | Track | Description |
| --- | --- | --- |
| 1 | **Agentverse** (sponsored by Fetch.ai) | Search & discovery of agents: build and register AI agents on Agentverse, discoverable via ASI:One, that turn user intent into real, executable outcomes. Optional, in addition to one of tracks 2–4. |
| 2 | **Model Learning** | Build systems that learn, adapt and improve from data. Create models that uncover patterns, make predictions or solve complex problems. |
| 3 | **Beyond the Digital** | Bring intelligence into the physical world: embedded AI, hardware, AR, VR or other emerging interfaces that make devices and environments more adaptive, interactive and immersive. |
| 4 | **Applied Intelligence** | Use AI to solve real-world problems beyond traditional AI applications: practical tools, products or systems for automation, accessibility, education, healthcare or any other meaningful use. |

The prizes for the overall winners and tracks 2–4 are listed on Devpost as "To Be Determined". The live site advertises "$45,000+ in prizes". Devpost's headline "$25,021,600" is a typo.

## Company challenges

Prize amounts come from each sponsor's challenge doc, which is more detailed than Devpost. Where they conflict, both are shown.

| Sponsor | Challenge | Prize | Hard requirements and judging |
| --- | --- | --- | --- |
| **Fetch.ai** | ASI:One Agent Challenge: From Intent to Action | $3,000 | Register ≥1 agent on agentverse.ai; implement the Agent Chat Protocol; be discoverable and usable through ASI:One; the **whole primary workflow must run inside an ASI:One conversation with no custom frontend**; show the interaction from asi1.ai; real tool execution or multi-agent orchestration (no thin chatbot wrappers); public GitHub repo; also submit through Fetch's Submission Agent. Bonus: multi-agent collaboration, Payment Protocol, ASI Interactive Cards, reliability, real-time data. [Doc](https://docs.google.com/document/d/18_z3Px6Vc0m6L2blLAk7DV8SelpGhoZy8t_8clSEroI/edit?tab=t.0) · [Hackpack](https://www.fetch.ai/events/hackathons/la-hacks-ai-hackathon-2026/hackpack) · [Submission process](https://docs.google.com/document/d/1UDW-X1C24hxZviFOQzjTeh0pXRNAoflMb8lhJqZP9Z0) |
| **Paper** | Best Designed Hack | 1st $1,500 · 2nd $1,000 · 3rd $500 | Judged on design fundamentals (hierarchy, legibility, consistency, contrast), ease of use, and personal craft, meaning it shouldn't look AI-generated. The page doesn't say the design must be made in Paper. Paper Pro free for a month with code `LAHACKS26`; Paper's desktop app exposes an MCP server so agents can read and write the canvas. [Page](https://paper.design/la-hacks) |
| **Cognition** | Best Use of Devin | $5,000 in **Devin credits** (Devpost says cash) | Build with Devin. Judged on creativity, novelty, polish. Every team gets free Devin credits. [Doc](https://docs.google.com/document/d/1E95qigDIP1YB4dP_j6e3QsTRc0pB2tgCSpvUd1GBO54/edit?usp=sharing) |
| **Base44** | Build Something People Want | 1st $1,500 · runner-up $500 | Must be **built substantially on Base44**, with a live Base44 app, a problem/user/solution write-up, and what you learned or changed while building. Rewards a real user, a working product, evidence of iteration. [Doc](https://docs.google.com/document/d/1SlIrPxU67Lc35i9OYpaVt7fdJTJIqt2Z6n9FyrzGyP0/edit?usp=sharing) · [Starter pack](https://base-builder-launch.base44.app/) |
| **QNX** | Best use of QNX | 1st $1,000 · two runners-up $250 | Embedded system that (1) runs QNX OS and (2) includes an open-source AI module from https://oss.qnx.com. QNX on Raspberry Pi is available at the event. [Doc](https://docs.google.com/document/d/1u0d-6YyJ1SzFu9b0myPdhUDPSyJhDg0pzgVMXqmbLtE/edit?usp=sharing) |
| **Workday** | Build the Future of Work with AI | $2,000 | An AI agent or prototype that helps people succeed after joining a company (ramping up, finding trusted info, everyday tasks, skills, growth). Need not use Workday. Weights: agentic logic 30%, new-hire relevance 20%, responsible AI & trust 20%, future-of-work relevance 15%, UX & inclusivity 10%, pitch 5%. Show the human-in-the-loop, why the AI recommended something, and what it won't do. [PDF](https://drive.google.com/file/d/1cwiVFY_8sYZdA4Vxr36Hi7kyhZMNVPPA/view?usp=sharing) |
| **Even Realities** | Smart Glasses Building Challenge ("Quiet Tech") | 1st: G2 glasses ×4 ($2,400) · 2nd: $250 OpenAI gift card each · 3rd: $100 each | Build an Even Hub app for Even G2 glasses; upload it to Even Hub as a Beta build; run it on a physical G2 at judging (loaners at their table); app name ≤20 chars and can't contain "Even"; no medical, financial or emergency-routing apps; demo video shows the G2 view; README covers install and keys. [Doc](https://docs.google.com/document/d/1mRDOVuKf-cMgaM4QsWaTrB_E5fMw44BoqDoHRBVLZh8/edit?usp=sharing) · [Starter pack](https://evenrealities-lahacks.vercel.app/starterpack) |
| **Visa** | The Future of Shopping: Powered by AI, Secured by Visa | $2,000 | GenAI commerce experience across discovery, decisions, personalization, checkout, payments, loyalty or post-purchase. Weights: innovation 25%, UX 25%, technical execution 20%, commerce impact 15%, trust & responsibility 15%. [Doc](https://docs.google.com/document/d/10vXJndQUMgbbc23v5NobI69DiV04nX62XKEHViC0ndA/edit?tab=t.0) |
| **Creao AI** | Best AI-First Disruptor / Best One-Person Company / Best Team Empowerment | $2,000 / $1,000 / $500 (Devpost lists $3,500 total) | Build on CREAO. Winners join the CREAO Launchpad program. [Upgraded signup](https://creao.ai/signup?hackathon=ucla-ai&utm_source=ucla-ai&utm_medium=hackathon&utm_campaign=hackathons-oct-2026) · [Details](https://community.creao.ai/AI_hackathon_UCLA2026?utm_source=ucla-ai&utm_medium=hackathon&utm_campaign=hackathons-oct-2026) |
| **veri.studio** | Best use of an Open-sourced model | $800 split across the team | Post-train or fine-tune an open model with Veri. Get credits by DMing `@daniung` in the LA Hacks Discord and redeem them **before** the first run. This repo has a Veri skill at [.claude/skills/veri/SKILL.md](.claude/skills/veri/SKILL.md). [Page](https://www.veri.studio/lahacks) |
| **Intuit** | QuickBooks: Reimagining Accounting with System One Models | 1st $200 · 2nd $100 · 3rd $50 gift card per person | Use a "System One" style model (fast, specialized, e.g. Jev) to make a new QuickBooks experience possible; you must design and run a realistic evaluation against classical ML or LLM baselines. Synthetic data: [Hugging Face dataset](https://huggingface.co/datasets/CL251215/QuickBooks-Hackathon-2026/tree/main). [Doc](https://docs.google.com/document/d/1JGmvJvZugbFrJW2WSrrPF96r_wB_xaMkfqVM49LE4nU/edit?usp=sharing) |
| **Sentry** | Best Use of Sentry | Guaranteed internship/new-grad interview per member | Use Sentry plus **at least two** products beyond error monitoring (Session Replay, Logs, Tracing, Profiling, Uptime, MCP/AI agent monitoring), and show how observability shaped the build. [Doc](https://docs.google.com/document/d/1JIlPd5vxcm8klztORkRX0FPXp4F865mxUbteJY8MUAw/edit?usp=sharing) |
| **Espressif** | Best Use of Espressif | Hardware (doc: ESP-VoCat, M5Stack Stopwatch; Devpost also lists an M5StackChan) | Use Espressif hardware (ESP32 boards; ESP-Claw at their Build Bar). [Doc](https://docs.google.com/document/d/1Qf9i2LGiDqHdEGf1eZ49hdrAIIpv3aaYOrJCPWoyMdw/edit?usp=sharing) |
| **StepFun** | Get It Done with Step 5 Preview | Not listed on Devpost | The app must call `step-5-preview` at runtime; explain what each other model or service does alongside it. Judged on task completion, reliability, user understanding and control. [Platform](https://platform.stepfun.ai/) |
| **Photon** | Build a Messaging/Calling Agent using Photon | Not listed on Devpost | Messaging or calling agent on Photon 2.0 beta (iMessage, SMS, RCS, Telegram, WhatsApp, email, phone). [Guidelines](https://somethingreat.notion.site/Hackathon-Guidelines-for-Photon-2-0-3f8e443f36bb81f9893fed0d08a4c01d?pvs=143) |
| **Browser Use** | Best Use of Browser Use | Not listed on Devpost | An agent built on Browser Use that turns a goal into action on the web; needs a working demo. [Site](https://browser-use.com/) |
| **MLH** | Best Domain Name (GoDaddy Registry), Gemini API, Snowflake API, ElevenLabs, Vultr, Solana, Tiger Data; plus the Commit Fellowship category | Hardware and swag (the MLH doc and Devpost list different items) | One prize each for best use of that technology. The Commit Fellowship category needs a working prototype, a real problem, opting in on Devpost, and a supplemental form. [Doc](https://docs.google.com/document/d/1a9TbDI0u8P2DGFFfoGXb9zEON5vrdm5PVK9yKufYLVo/edit?usp=sharing) |

### Fit with this repo (our judgment, not organizer guidance)

This repo is an Expo (React Native) mobile app. Against that:

- **Natural fits:** Applied Intelligence (main track), Paper (design), Visa, Workday, Sentry (has a React Native SDK), Cognition/Devin, StepFun, MLH Gemini / ElevenLabs / GoDaddy, and Veri if part of the project fine-tunes a model.
- **Possible with a separate backend piece:** Fetch.ai (the agent must work entirely inside ASI:One, so the mobile app can't be the required interface), Photon, Browser Use, Intuit.
- **Poor fits:** Base44 (must be built on Base44), Even Realities (must be an Even Hub app on G2), QNX and Espressif (embedded hardware). Beyond the Digital as the main track needs hardware or AR/VR.

## Sponsors

From the live site, grouped by the site's logo tier.

- **Large:** Fetch.ai, Paper, Annapurna Labs (Amazon), AWS
- **Medium:** Cognition, QNX, Even Realities, Base44, Workday, StepFun
- **Small:** Alma, Pure Buttons, MLH, Espressif, Photon, Visa, Adobe, a16z speedrun, a16z Alpha, Pebblebed, Accenture, Creao, Sentry, Browser Use, Nami Matcha, AppLovin, Intuit
- **Not on the sponsor list but runs a challenge:** veri.studio

## Schedule (all times PDT)

All workshops are on the 2nd Floor Patio and all meals on the Collins Patio (1st floor) unless noted.

### Saturday, Oct 17

| Time | Event | Where |
| --- | --- | --- |
| 9:00–11:00 AM | Check-in | Alumni Center front entrance |
| 11:00 AM–12:00 PM | Opening ceremony | Collins Conference Room |
| **12:00 PM** | **Hacking starts** | |
| 12:00–1:00 PM | Lunch (Emporium Thai) · Team formation (2nd Floor Patio) | |
| 1:00–2:00 PM | [Fetch.ai] Build, Deploy & Monetise AI Agents | |
| 1:00–8:00 PM | Mentors mainly available (open a ticket in Discord `#mentor-info`) | |
| 2:00–3:00 PM | Annapurna Labs workshop | |
| 3:00–4:00 PM | [Even Realities] Build for the Glasses of the Future | |
| 3:30–4:00 PM | [MLH] Tech Together meetup | |
| 4:00–5:00 PM | [QNX] Embedded Development with QNX | |
| 5:00–6:00 PM | Dinner (Chipotle) · [Espressif] Build Bar | |
| 6:00–7:00 PM | [Workday] Workday AI in Action | |
| 7:00–8:00 PM | [Cognition] How to Build Fast with AI (Devin demo, credits tips) | |
| 7:30–8:00 PM | AppLovin snack drop (boba, cookies) | Collins Patio |
| 8:00–9:00 PM | [StepFun] Build Your First Agent with Step 5 Preview | |
| 9:00–10:00 PM | [Creao AI] From Chat to Backend: Build an AI Agent You Can Call From Code | |
| 10:00–11:00 PM | Roblox Dress to Impress showdown (Fetch.ai) | |
| 11:00 PM–12:00 AM | Late-night matcha (Nami Matcha) | Collins Patio |

### Sunday, Oct 18

| Time | Event | Where |
| --- | --- | --- |
| 12:00–1:00 AM | Poker (Founders Room) · Karaoke (2nd Floor Patio) | |
| 8:00–9:00 AM | Morning matcha | Collins Patio |
| 9:00–9:30 AM | [MLH] Hacking with GitHub Copilot | |
| 9:30–10:00 AM | [MLH] Intro to Google AI Studio | |
| 11:00 AM–12:00 PM | Brunch (Fresh Corn Grill) | Collins Patio |
| **12:00 PM** | **Hacking ends. Devpost submission deadline.** | |
| 12:30–2:00 PM | Judging round 1: Science Fair | Alumni Center |
| 2:00–3:00 PM | Judging round 2: Top 5 Demos | Alumni Center |
| 3:00–4:00 PM | Closing ceremony | Collins Conference Room |

## Venue and logistics

- **Venue:** James West Alumni Center (JWAC), UCLA, 325 Westwood Plaza, Los Angeles, CA 90095. Map: https://live.lahacks.com/map
- **Wi-Fi:** outside, `LA HACKS` (no password). Inside, `UCLA_WEB`, `UCLA_WIFI` or `eduroam`.
- **No sleeping area and no showers.** Re-entry is allowed with a visible badge.
- **Hardware:** some sponsors lend hardware, in limited supply. No 3D printers.
- **Help:** Discord `#ask-an-organizer` (general), `#mentor-info` and `#find-a-mentor` (mentors), info@lahacks.com (personal), or organizers in dark blue LA Hacks shirts.
- **Links:** [Live site](https://live.lahacks.com) · [Tracks](https://live.lahacks.com/tracks) · [Devpost](https://la-ai-hackathon-2026.devpost.com/) · [Discord](https://discord.gg/VcWYpcGtAB) · [Hacker guide](https://docs.google.com/document/d/e/2PACX-1vRoCKR0WuXMLeXZ4S_aUbi7VbMMxHJioNu5QWzfZXxEAB4uXsS5DDhKhp5MJzJPeDrnWwdbmX4d4Hoy/pub) · [MLH Code of Conduct](https://github.com/MLH/mlh-policies/blob/main/code-of-conduct.md)
- **About the event:** LA Hacks' first AI Hackathon. 2000+ participants, about 200 projects expected. Keynotes: Evan Spiegel, Michael Yan.

## Repo facts that affect the build

- **Stack:** Expo SDK 58 (`expo ~58.0.14`), React Native 0.88, React 19.3, TypeScript 6 (strict). npm (`package-lock.json`), so use `npx`, not `bunx`.
- **Follow [AGENTS.md](AGENTS.md):** read the Expo v58 docs before touching any Expo API; add packages with `npx expo install`; run `npx expo lint` and `npx tsc --noEmit` before calling a task done.
- **Routing is not set up yet.** The repo is still the blank template: [index.ts](index.ts) registers [App.tsx](App.tsx). AGENTS.md asks for Expo Router with routes in `src/app/`, so migrating to Expo Router is the first structural task. Do it once, before parallel feature work starts.
- **Demo device:** Expo Go only bundles certain native modules. A library with custom native code needs a development build, which costs time to set up. Prefer libraries that work in Expo Go unless a feature truly needs native code.
- **Venue Wi-Fi:** if a phone can't reach the dev server on campus Wi-Fi, run `npx expo start --tunnel`. Test this early, not at 11:50 AM Sunday.
- **Secrets:** the repo has to be public for submission. Never commit API keys; put them in `.env.local` ([.gitignore](.gitignore) ignores `.env*.local`, but not a plain `.env`). Anything a phone app ships can be read, so expensive API keys belong behind a small backend.
