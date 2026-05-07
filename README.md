# Murmura

<div align="center">

**Turn any text into a simulated world of people, incentives, reactions, and possible futures.**

**將任何文字變成一個可模擬的世界：人物、動機、反應、風險同可能未來。**

[![License](https://img.shields.io/badge/license-Prosperity%20Public%202.0-orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3-brightgreen)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)](https://fastapi.tiangolo.com/)

### Choose your language

[English](#english) | [中文](#中文)

</div>

---

<a id="english"></a>

## English

### What Is Murmura?

Murmura is a universal prediction engine for exploring how groups may react to events, shocks, policies, stories, and market changes.

You paste in a piece of text. Murmura turns it into a simulated world.

That text can be:

- a news article
- a market shock
- a policy proposal
- a company memo
- a conflict scenario
- a fictional world
- a historical fragment
- a question you want to stress-test

Murmura then asks: who matters, who is affected, what do they believe, how do they influence each other, what could change, and which outcomes look more or less likely?

In plain language: **Murmura helps you explore “what might happen next?” without manually building a simulation from scratch.**

### What Can You Do With It?

| You want to know... | Murmura helps by... |
|---|---|
| How different groups may react to an event | Creating agents with different roles, incentives, beliefs, and memories |
| Which hidden stakeholders are being missed | Finding actors who are affected even if they are not named in the text |
| How a shock could spread through a system | Simulating rounds of reaction, belief change, faction formation, and feedback |
| Whether a result is stable or fragile | Running branches, what-if scenarios, and probability bands |
| Why the forecast says what it says | Producing traceable reports with evidence, timelines, and agent reasoning |
| What a specific actor might say or do | Letting you interview simulated agents after the run |

Example inputs:

```text
A new competitor enters a B2B supply chain market with aggressive pricing.
```

```text
A central bank unexpectedly raises interest rates by 200 basis points.
```

```text
In a fictional kingdom, two factions compete for control after the monarch disappears.
```

### How It Works

Murmura uses a five-step workflow:

```text
1. Build the world
   Your text becomes a knowledge graph of people, organizations, events, places, and relationships.

2. Create the agents
   The system creates simulated actors with goals, memories, personalities, beliefs, and platform identities.

3. Run the simulation
   Agents react over multiple rounds. They make decisions, influence each other, form factions, and respond to shocks.

4. Generate the report
   Murmura explains what happened, what changed, what outcomes emerged, and where the uncertainty is.

5. Ask follow-up questions
   You can interview agents, test what-if shocks, and compare alternative timelines.
```

You do not need to configure agents, decisions, metrics, or shocks by hand. Murmura infers them from the seed text.

### Quick Start

#### Option 1: Local Development

Requirements:

- Python 3.10 or 3.11
- Node.js 18+
- Git

```bash
git clone https://github.com/destinyfrancis/Murmura.git
cd Murmura
make quickstart
```

Daily development:

```bash
make start      # start backend :5001 and frontend :5173
make stop       # stop local services
make backend    # backend only
make frontend   # frontend only
```

Open the app at:

```text
http://localhost:5173
```

#### Option 2: Docker

```bash
cp .env.example .env
docker compose up -d
```

Demo mode without live API keys:

```bash
docker compose --profile demo up -d
```

With observability:

```bash
docker compose --profile observability up -d
```

### API Keys And Models

Murmura can run in demo mode, but live LLM-powered runs need model provider keys.

The easiest path:

1. Copy `.env.example` to `.env`.
2. Add your provider keys.
3. Start the app.
4. Open **Settings** in the UI to test keys and change models.

Common settings:

| Setting | What it controls |
|---|---|
| `OPENROUTER_API_KEY` | Agent generation and agent decisions |
| `GOOGLE_API_KEY` | Report generation, if using Google models |
| `AGENT_LLM_PROVIDER` | Default provider for agents |
| `AGENT_LLM_MODEL` | Main agent model |
| `AGENT_LLM_MODEL_LITE` | Cheaper model for background agents |
| `LLM_PROVIDER` | Default provider for reports |
| `AUTH_SECRET_KEY` | JWT signing key for auth |

You can also set different models for each workflow step from the Settings page.

### Main Features

- **Universal input**: paste almost any scenario, article, memo, or story.
- **Automatic actor discovery**: finds visible and hidden stakeholders.
- **Knowledge graph**: shows entities and relationships behind the simulation.
- **Agent-based simulation**: runs many agents with different incentives and memories.
- **Belief and faction dynamics**: tracks how views spread, harden, or split.
- **Shock testing**: inject policy, market, social, or narrative shocks.
- **What-if branches**: compare alternative timelines.
- **Probability bands**: read uncertainty instead of a single fake-certainty answer.
- **Explainable reports**: generate reports that show reasoning and evidence.
- **Agent interviews**: ask simulated agents why they acted or changed beliefs.
- **Runtime settings**: change API keys, models, and presets without restarting.

### Example Use Cases

| Area | Example |
|---|---|
| Policy | “What groups may support or oppose this housing policy?” |
| Markets | “How could a sudden rate hike affect investor sentiment?” |
| Companies | “How may customers, suppliers, and competitors react to a new entrant?” |
| Geopolitics | “Which actors may escalate, de-escalate, or hedge after this event?” |
| Public narrative | “How might a message spread across communities?” |
| Fiction and worldbuilding | “How would factions in this story respond to a major shock?” |
| Research | “Which assumptions matter most in this scenario?” |

### Simulation Presets

| Preset | Agents | Rounds | Best for |
|---|---:|---:|---|
| FAST | 100 | 15 | Quick demos and smoke tests |
| STANDARD | 300 | 20 | General analysis |
| DEEP | 500 | 30 | More detailed research runs |
| LARGE | 1,000 | 25 | Larger stress tests |
| MASSIVE | 3,000 | 20 | Heavy simulations |
| custom | up to 50,000 | up to 100 | Advanced experiments |

Note: the OASIS simulation engine currently requires Python 3.10 or 3.11. On Python 3.12+, the UI will gracefully disable the Simulation step instead of crashing.

### Project Structure

```text
backend/
  app/api/          FastAPI routes
  app/services/     simulation, graph, report, settings, and analytics logic
  app/models/       Pydantic request and response models
  app/utils/        database, LLM, logging, and security helpers
  database/         SQLite schema
  tests/            pytest tests

frontend/
  src/views/        main pages
  src/components/   reusable UI components
  src/api/          frontend API clients
  src/i18n/         Traditional Chinese and English copy

data/
  benchmarks/       benchmark fixtures
```

### Useful Commands

```bash
make test          # unit tests
make test-int      # integration tests
make test-all      # full test suite
make test-cov      # coverage report
make test-changed  # tests related to changed files
```

Frontend:

```bash
cd frontend
npm run build
npm run dev
```

### Release Status

This repository is ready as a public source release, but it is not currently an npm/PyPI package.

Current distribution path:

- clone the repository
- run locally with `make quickstart`
- or run with Docker Compose

Package publishing would need a separate packaging pass, including package entrypoints, published artifacts, versioning rules, and registry metadata.

### Important Limits

Murmura is for exploration, research, and scenario stress-testing. It is not a replacement for professional judgment.

Do not use it as the only basis for:

- financial trading
- legal advice
- medical decisions
- safety-critical decisions
- regulatory or actuarial reporting

Good simulations need good input. Include context, time horizon, actors, uncertainty, and the question you actually care about.

### License

Prosperity Public License 2.0.0.

Non-commercial personal, academic, and non-profit use is permitted. Commercial or revenue-generating use requires a separate commercial license.

Copyright © 2026 destinyfrancis. All rights reserved.

---

<a id="中文"></a>

## 中文

### Murmura 是什麼？

Murmura 是一個通用預測引擎，用來探索不同群體面對事件、衝擊、政策、故事或市場變化時，可能會有什麼反應。

你只需要貼入一段文字，Murmura 就會把它變成一個可模擬的世界。

這段文字可以是：

- 新聞文章
- 市場衝擊
- 政策建議
- 公司備忘錄
- 衝突場景
- 虛構世界
- 歷史片段
- 一條你想壓力測試的問題

Murmura 會從文字入面推斷：誰重要、誰受影響、他們相信什麼、他們如何互相影響、什麼因素可能改變局勢，以及哪些結果看起來較可能或較不可能。

簡單講：**Murmura 幫你探索「接下來可能會發生什麼？」而不需要你手動建立整個模擬。**

### 它可以做什麼？

| 你想知道... | Murmura 會幫你... |
|---|---|
| 不同群體會如何回應某件事 | 建立有不同角色、利益、信念和記憶的代理人 |
| 有沒有被忽略的持份者 | 找出文本沒有明講、但其實會受影響的人或組織 |
| 一個衝擊會如何擴散 | 模擬多輪反應、信念變化、派系形成和連鎖回饋 |
| 結果是否穩定，還是很脆弱 | 跑分支、what-if 情景和概率區間 |
| 為什麼系統會得出這個預測 | 生成有證據、時間線和代理人推理的報告 |
| 某個角色可能會怎樣想或怎樣做 | 在模擬後訪談指定代理人 |

輸入例子：

```text
一個新競爭者以激進定價進入 B2B 供應鏈市場。
```

```text
中央銀行突然加息 200 個基點。
```

```text
在一個虛構王國中，君主失蹤後兩大派系開始爭奪控制權。
```

### 運作方式

Murmura 使用五步工作流：

```text
1. 建立世界
   你的文字會變成一個知識圖譜，包含人物、組織、事件、地點和關係。

2. 建立代理人
   系統會建立有目標、記憶、性格、信念和平台身份的模擬角色。

3. 運行模擬
   代理人會在多個回合中反應、決策、互相影響、形成派系並回應衝擊。

4. 生成報告
   Murmura 會解釋發生了什麼、什麼改變了、出現了哪些結果，以及不確定性在哪裡。

5. 追問和互動
   你可以訪談代理人、測試 what-if 衝擊，並比較不同時間線。
```

你不需要手動設定代理人、決策、指標或衝擊。Murmura 會從種子文字自動推斷。

### 快速開始

#### 方式一：本地開發

需求：

- Python 3.10 或 3.11
- Node.js 18+
- Git

```bash
git clone https://github.com/destinyfrancis/Murmura.git
cd Murmura
make quickstart
```

日常開發：

```bash
make start      # 啟動 backend :5001 和 frontend :5173
make stop       # 停止本地服務
make backend    # 只啟動後端
make frontend   # 只啟動前端
```

打開應用：

```text
http://localhost:5173
```

#### 方式二：Docker

```bash
cp .env.example .env
docker compose up -d
```

無需真實 API key 的 demo mode：

```bash
docker compose --profile demo up -d
```

啟用 observability：

```bash
docker compose --profile observability up -d
```

### API Key 與模型設定

Murmura 可以用 demo mode 試用，但如果要跑真實 LLM 模擬，就需要模型供應商的 API key。

最簡單流程：

1. 將 `.env.example` 複製成 `.env`。
2. 加入你的 provider keys。
3. 啟動應用。
4. 到 UI 的 **Settings** 測試 API key 和切換模型。

常用設定：

| 設定 | 用途 |
|---|---|
| `OPENROUTER_API_KEY` | 代理人生成和代理人決策 |
| `GOOGLE_API_KEY` | 如果使用 Google 模型，會用於報告生成 |
| `AGENT_LLM_PROVIDER` | 代理人預設 provider |
| `AGENT_LLM_MODEL` | 主要代理人模型 |
| `AGENT_LLM_MODEL_LITE` | 背景代理人使用的較低成本模型 |
| `LLM_PROVIDER` | 報告生成預設 provider |
| `AUTH_SECRET_KEY` | Auth JWT 簽名 key |

你亦可以在 Settings 頁面為每一個工作流步驟設定不同模型。

### 主要功能

- **通用輸入**：可以貼入場景、文章、備忘錄或故事。
- **自動尋找持份者**：找出明示和隱含的受影響角色。
- **知識圖譜**：顯示模擬背後的實體與關係。
- **多代理人模擬**：讓大量有不同利益和記憶的代理人互動。
- **信念與派系動態**：追蹤觀點如何傳播、強化或分裂。
- **衝擊測試**：注入政策、市場、社會或敘事衝擊。
- **What-if 分支**：比較不同時間線。
- **概率區間**：不要只看單一答案，而是看不確定性。
- **可解釋報告**：生成包含推理和證據的報告。
- **代理人訪談**：詢問模擬角色為什麼這樣行動或改變信念。
- **即時設定**：不重啟伺服器也可以更換 API key、模型和 preset。

### 使用例子

| 領域 | 例子 |
|---|---|
| 政策 | 「哪些群體可能支持或反對這個住房政策？」 |
| 市場 | 「突然加息會如何影響投資者情緒？」 |
| 公司策略 | 「客戶、供應商和競爭對手會如何回應新進入者？」 |
| 地緣政治 | 「這次事件後，哪些角色可能升級、降溫或對沖？」 |
| 公共敘事 | 「某個訊息會如何在不同社群中擴散？」 |
| 小說和世界觀 | 「故事中的派系面對重大衝擊會怎樣反應？」 |
| 研究 | 「這個情景裡哪些假設最關鍵？」 |

### 模擬 Preset

| Preset | 代理人 | 回合 | 適合用途 |
|---|---:|---:|---|
| FAST | 100 | 15 | 快速 demo 和 smoke test |
| STANDARD | 300 | 20 | 一般分析 |
| DEEP | 500 | 30 | 較深入研究 |
| LARGE | 1,000 | 25 | 較大型壓力測試 |
| MASSIVE | 3,000 | 20 | 重型模擬 |
| custom | up to 50,000 | up to 100 | 進階實驗 |

注意：OASIS simulation engine 目前需要 Python 3.10 或 3.11。如果使用 Python 3.12+，UI 會安全降級並停用 Simulation 步驟，而不是直接崩潰。

### 專案結構

```text
backend/
  app/api/          FastAPI routes
  app/services/     simulation, graph, report, settings, analytics logic
  app/models/       Pydantic request and response models
  app/utils/        database, LLM, logging, security helpers
  database/         SQLite schema
  tests/            pytest tests

frontend/
  src/views/        main pages
  src/components/   reusable UI components
  src/api/          frontend API clients
  src/i18n/         Traditional Chinese and English copy

data/
  benchmarks/       benchmark fixtures
```

### 常用命令

```bash
make test          # unit tests
make test-int      # integration tests
make test-all      # full test suite
make test-cov      # coverage report
make test-changed  # 只跑與改動相關的測試
```

前端：

```bash
cd frontend
npm run build
npm run dev
```

### 發布狀態

這個 repo 已適合作為 public source release，但目前不是 npm/PyPI package。

目前發布方式：

- clone repository
- 用 `make quickstart` 本地運行
- 或用 Docker Compose 運行

如果要正式做 package publish，仍需要額外處理 package entrypoints、發布 artifacts、版本規則和 registry metadata。

### 重要限制

Murmura 適合探索、研究和情景壓力測試。它不是專業判斷的替代品。

不要把它作為以下事情的唯一依據：

- 金融交易
- 法律意見
- 醫療決策
- 安全關鍵決策
- 監管或精算報告

好的模擬需要好的輸入。請盡量提供背景、時間範圍、角色、不確定性，以及你真正想回答的問題。

### License

Prosperity Public License 2.0.0.

非商業個人、學術和非牟利用途可以免費使用。商業或營利用途需要另外取得商業授權。

Copyright © 2026 destinyfrancis. All rights reserved.
