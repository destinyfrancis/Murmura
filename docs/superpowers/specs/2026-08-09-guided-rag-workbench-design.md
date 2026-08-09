# Murmura Guided RAG Workbench Design

**日期：** 2026-08-09

**狀態：** 已按用戶方向收斂，等待書面規格確認後進入 implementation plan

**產品定位：** 預設零研究門檻、主畫面持續顯示互動式 RAG graph；進階用戶可展開完整而科學化的實驗與驗證路徑。

## 1. 已確認產品決策

1. 不採用八字，亦不把任何玄學分類放入核心架構。
2. 吸收 MiroFish 的五步 guided workflow、持續可見世界模型、漸進式揭露、可理解進度與完成後互動等產品原則。
3. MiroFish 與 Murmura 同屬 AGPL v3 系列，允許在逐檔授權及技術審核後直接重用合適 code。重用內容必須保留原 copyright／license notices、標示修改日期與 upstream commit，並確保整個發佈及網絡服務繼續提供相應源碼。不得直接取用未確認授權的 assets、screenshots、商標或品牌文案。
4. 一般用戶預設不需要理解模型選擇、replicas、random seeds、backtest 或 sensitivity settings。
5. 進階用戶可在同一工作流程展開 Expert 路徑，選擇最完整的實驗與科學驗證設定。
6. 科學可信度不是視覺標籤：沒有真實 evidence 時必須 fail closed，顯示「未驗證」，不可用假預設值合成信心分數。

## 2. 成功準則

### 2.1 一般用戶

- 從 `/process/quick` 進入後，每一步只有一個清晰主要動作。
- 不需打開 Settings 或填寫研究參數即可完成 seed → graph → environment → simulation → result → interaction。
- Desktop 每一步都看得到同一個真實 RAG graph；切換步驟不重建 graph instance 或丟失 zoom、selection、filters。
- Mobile 每一步都可一鍵展開 graph，並保留目前 node selection 與時間點。
- 所有長時間工作都有具體中間產物、進度、可取消或可重試狀態，不能只顯示 spinner。
- 報告完成後仍可點 graph evidence、比較分支、訪問 agents 及追問 report。

### 2.2 進階用戶

- 可由工作台開啟 Expert drawer，不離開五步流程。
- 可檢視及調整 population、agent/round preset、model routing、shocks、replicas、validation 與成本相關設定；只顯示當前步驟可用的控制。
- 可查看 experiment manifest、模型與資料版本、randomness／replica 資訊、驗證缺口及 evidence provenance。
- 可前往完整 God View，但 Expert drawer 本身已足以完成一個可重現實驗。

### 2.3 科學可信度

- 沒有 backtest、ensemble 或 provenance 資料時，不可製造預設值。
- 每個結果明確屬於以下其中一級：
  - `scenario_exploration`：情景探索，沒有預測準確度宣稱。
  - `model_estimate`：有重複模擬與 uncertainty evidence，但未完成歷史校準。
  - `calibrated_forecast`：指定 domain／metric 有有效 backtest、baseline comparison 與 calibration evidence。
- 趨勢卡必須同時顯示 horizon、direction、magnitude／range、支持與反對證據、stability，以及 credibility tier。
- generic seed 不得因為 agents 數量多或 agent consensus 高，就標示為 calibrated forecast。

## 3. 現況與主要缺口

Murmura 已有 GraphRAG、五步流程、temporal graph、node evidence、simulation hooks、ensemble、backtest、sensitivity、validation、report、agent interview 與 God View。升級以重組和補可信合約為主，不重寫引擎。

已確認缺口：

- `frontend/src/views/Process.vue` 只 mount 當前 Step component；真實 `GraphPanel` 只存在於 Step 1 和 Step 3。
- Express mode 的 `WorkflowGraphPulse` 是流程示意圖，不是可查詢的 RAG graph。
- Step 2、4、5 缺少持續可見的真實 world graph，使用者失去空間連續性。
- Advanced views 依賴 `?advanced=1`，不是可發現、可保存的產品模式。
- 科學能力散落於 `PredictionDashboard`、`GodViewTerminal`、`CrossDomainValidationPanel`、`SensitivityPanel` 等位置，沒有連成核心流程。
- `backend/app/api/validation.py` 在 evidence 缺失時代入 MC 與 Theil's U 假預設值。
- `backend/app/services/confidence_assessor.py` 在未 backtest 時固定使用 `model_fit=0.7`，亦會在沒有 decisions 時合成 baseline score。
- `backend/app/api/simulation_macro.py` 接受 caller 傳入 `confidence_score=0.5`／`confidence_level=medium`，LLM narrative 因此可以收到未經驗證的信心設定。
- `frontend/src/components/TrendReport.vue` 無視目前 domain，固定載入香港宏觀指標回測，可能把無關的準確度顯示在 generic scenario。
- `frontend/src/api/simulation.js` 呼叫不存在的 `/confidence-score` route。
- ReportAgent 的 validation summary 使用全域 calibration hit rate，沒有證明該數字與目前 session、claim、domain、metric、horizon 相符。
- `WorkflowRunner` 在 runtime 自行建立 workflow tables，而 `Process.vue` 同時用本地 `nextStep()` 與 server `step_index` 推進，形成兩套 workflow truth。
- `Process.vue`、Step 1–4 components 已超過 project 的 800-line 上限；MiroFish 對應 components 亦是大型單檔。即使直接重用其中 interaction code，仍要沿 Murmura 責任邊界拆細，避免移植 monolith。
- 部分 graph labels 與 confidence UI strings 仍然 hardcode，違反 i18n 規則。

## 4. 體驗架構

### 4.1 固定工作台外殼

Desktop 採用三個穩定區域：

```text
┌──────────────────────────────────────────────────────────────┐
│ Header: Step / status / Guided-Expert / cost & credibility   │
├───────────────────────────────────┬──────────────────────────┤
│ Persistent RAG Graph Workspace    │ Current Step Panel       │
│                                   │ one primary action       │
│ graph toolbar / evidence drawer   │ progress / outputs       │
├───────────────────────────────────┴──────────────────────────┤
│ Evidence & trend strip / system status / current artefacts   │
└──────────────────────────────────────────────────────────────┘
```

- Graph 預設佔較大面積，右邊 step panel 保持可掃讀。
- 報告及 interaction 階段可拖動或切換比例，但 graph 不會 unmount。
- Step transition 只更換右側 task panel 與 graph overlay mode。
- Graph 的 camera、selected node、filters、round、community overlay 存在 shared composable/store。
- Evidence detail 使用 side drawer 或 inline inspector，不用 modal 阻斷流程。

Mobile：

- Step panel 是預設頁面。
- Graph 是固定可見的「Graph」tab／bottom sheet，不是另一路由。
- 切換時保留 graph state。

### 4.2 Guided 與 Expert

`Guided` 是唯一預設：

- 系統自動建議 domain、population、preset、模型路由與 validation path。
- 每步只顯示必要解釋、目前產物、預計時間／成本及一個主要 CTA。
- 自動設定必須可以在提交前用 plain language 檢視。

`Expert` 是同一工作台的 progressive disclosure：

- Header 有清楚的 Expert toggle；狀態保存到 `localStorage('murmura_workbench_mode')`。
- Expert drawer 只顯示與當前 step 有關的設定，不建立第二套 workflow。
- 設定分四組：World & population、Experiment、Models & cost、Validation & provenance。
- 改變會影響可重現性的設定後，manifest 顯示 dirty 狀態；再次運行才建立新 result，不能靜默改寫已完成結果。

## 5. 五步產品流程

### Step 1 — Reality seed → World graph

Guided：輸入／上載材料、確認預測問題、啟動 graph build。Graph 逐步顯示 explicit nodes、implicit actors、edges 與 provenance 狀態。

Expert：domain pack、extractor/model override、hidden actor review、source scope 與 knowledge-firewall diagnostics。

主要產物：`graph_id`、graph quality summary、source/provenance coverage、scenario question。

### Step 2 — World graph → Population & experiment

Guided：顯示自動生成的角色數、主要群體、時間範圍、rounds、預計時間及成本；接受建議後建立 simulation。

Expert：agent distribution、platforms、shocks、preset/custom counts、replica strategy、models、cost cap，以及 experiment manifest preview。

Graph overlay：把 KG nodes 與 generated agents／platform identities 的對應關係可視化。

主要產物：`session_id`、frozen experiment manifest、agent/profile summary。

### Step 3 — Live simulation

Guided：graph、事件流、round progress、主要趨勢、暫時性不確定範圍與停止／恢復控制。

Expert：hooks、factions、belief propagation、ensemble／fork status、stability diagnostics、raw tool events 與 resource usage。

Graph overlay：temporal changes、community hulls、events、contagion、selected round。

主要產物：timeline、actions、metrics、replica／ensemble evidence、completed simulation state。

### Step 4 — Evidence-backed result

Guided：先顯示結論、方向、範圍、credibility tier、主要原因與限制；報告生成進度顯示 sections、evidence count、tool status，而不是私有 chain-of-thought。

Expert：backtest、baseline comparison、calibration、sensitivity、provenance、missing evidence、XAI tool records 與 report manifest。

Graph overlay：報告引用的 nodes／edges、支持／反對 evidence、可點擊來源。

主要產物：`report_id`、claim-level evidence、PDF/share、validation summary。

### Step 5 — Explore & interact

Guided：Report chat、agent interview、branch comparison 三個清晰入口，並保留各自對話。

Expert：群體 survey、memory search、What-If fork、scenario comparator、selected evidence context。

Graph overlay：對話目標、相關群體、引用 evidence 與 branch differences。

主要產物：可保存的問答／訪談、branch request、比較結果。

## 6. 科學與趨勢資料合約

### 6.1 Fail-closed validation

修改 confidence API，使缺失資料保持 `null`／`unavailable`：

```json
{
  "credibility_tier": "scenario_exploration",
  "confidence_score": null,
  "signals": {
    "backtest": { "status": "missing", "value": null },
    "ensemble": { "status": "missing", "value": null },
    "consensus": { "status": "available", "value": 0.42 },
    "provenance": { "status": "partial", "value": 0.61 }
  },
  "missing_evidence": ["backtest", "ensemble"],
  "limitations": ["此結果只可作情景探索"]
}
```

- `agent_consensus` 只代表群體一致程度，不代表對真實世界的準確度。
- 未完成 backtest 時 `model_fit` 必須是 `null`，不能使用 `0.7`。
- `calibrated_forecast` 要求相同 domain／metric／horizon 的有效歷史驗證，且 beats-naive evidence 可查閱。
- 舊 client 所需欄位如要保留，必須標記 deprecated；不可把 `null` 轉成中信心。

### 6.2 Trend signal

Backend 先產生不可變的 structured claim，LLM 只可解釋，不可改寫 direction、estimate、interval、tier 或 validation status：

```ts
type TrendClaim = Readonly<{
  claimId: string
  sessionId: string
  metric: string
  horizon: string
  direction: 'up' | 'down' | 'flat' | 'uncertain'
  estimate: number | null
  interval: readonly [number, number] | null
  credibilityTier: 'scenario_exploration' | 'model_estimate' | 'calibrated_forecast'
  validationStatus: 'not_applicable' | 'pending' | 'passed' | 'failed' | 'insufficient_evidence'
  evidenceIds: readonly string[]
  counterSignals: readonly string[]
  methodVersion: string
  manifestId: string
}>
```

工作台再把 claim 映射成單一 frontend display contract：

```ts
type TrendSignal = Readonly<{
  metric: string
  horizon: string
  direction: 'up' | 'down' | 'flat' | 'uncertain'
  centralEstimate: number | null
  interval: readonly [number, number] | null
  stability: 'stable' | 'mixed' | 'unstable' | 'not_assessed'
  credibilityTier: 'scenario_exploration' | 'model_estimate' | 'calibrated_forecast'
  supportingEvidence: readonly EvidenceRef[]
  opposingEvidence: readonly EvidenceRef[]
  limitations: readonly string[]
}>
```

所有 report、trend strip、confidence UI 與 export 都使用同一組語義，避免同一 session 在不同頁顯示不同「信心」。

## 7. Component 與責任邊界

### 7.1 新增 frontend units

- `frontend/src/components/workbench/ProcessWorkbenchShell.vue`：純 layout slots，不持有 domain logic。
- `frontend/src/components/workbench/WorkbenchHeader.vue`：step、status、Guided/Expert、cost、credibility。
- `frontend/src/components/workbench/PersistentGraphWorkspace.vue`：唯一 graph mount、toolbar、overlay mode、empty/loading/error state。
- `frontend/src/components/workbench/StepTaskPanel.vue`：目前 step container、primary action 與 step progress。
- `frontend/src/components/workbench/ExpertControlDrawer.vue`：按 step 顯示 expert sections。
- `frontend/src/components/workbench/ScientificEvidenceStrip.vue`：trend、tier、evidence completeness、limitations。
- `frontend/src/components/workbench/GraphEvidenceDrawer.vue`：node／edge provenance 與引用。
- `frontend/src/composables/useProcessWorkflow.js`：workflow/session state、navigation、express polling、cleanup。
- `frontend/src/composables/useGraphWorkspace.js`：graph data、camera/selection/filter/round state。
- `frontend/src/composables/useWorkbenchMode.js`：Guided/Expert persistence 與 dirty-manifest guard。
- `frontend/src/api/validation.ts`：typed credibility/trend contract。

### 7.2 修改與拆分

- `frontend/src/views/Process.vue` 只負責 composition；目標少於 400 lines。
- Step 1–4 保留既有 business logic，但把 form、progress、result、advanced sections 拆成 focused subcomponents；所有 touched files 不超過 800 lines。
- `GraphPanel.vue` 移除 hardcoded labels，接收 i18n labels／controls，並成為 persistent workspace 的可重用 renderer。
- Step 1／3 不再各自 mount `GraphPanel`，改以 events/state 驅動 persistent graph。
- `WorkflowGraphPulse` 保留為 express telemetry overlay，但不能代替真實 RAG graph。
- 重用 `ConfidenceBadge`、`CrossDomainValidationPanel`、`SensitivityPanel`、`EnsembleChart`、`ScenarioComparison` 的能力；統一文案與 credibility contract，不建立重複分析引擎。

### 7.3 Backend units

- 修改 `backend/app/api/validation.py`：移除 fabricated defaults，回傳 evidence availability 與 tier。
- 修改 `backend/app/models/validation.py`：以 frozen models 表達 nullable signals、missing evidence、tier、limitations。
- 修改 `backend/app/services/confidence_assessor.py`：model fit 來自真實 backtest；缺失時保持 unavailable。
- 修改 `backend/app/api/simulation_macro.py`：confidence 不再由 query parameter 輸入，narrative 只讀已保存的 structured claim。
- 新增 `backend/app/models/trend_claim.py`、`backend/app/services/trend_analysis.py` 與 `backend/app/services/scientific_validation.py`，產生 session/claim-scoped 結果。
- 新增薄 router `backend/app/api/analysis.py`：
  - `GET /api/analysis/{session_id}/claims`
  - `GET /api/analysis/{session_id}/credibility`
  - `POST /api/analysis/{session_id}/validate`
- Probability forecast 使用 Brier／log score；continuous forecast 使用 CRPS／interval coverage；directional accuracy 只可作輔助證據。
- Workflow state 由 backend 成為唯一 source of truth。`workflow_runs`／`workflow_events` 進入正式 schema/migration；event 有遞增 ID，client 只拉取 `after_event_id` 之後的 events。
- Guided／Expert 使用同一 workflow、manifest、session 與 claim contract，不建立第二套 backend path。
- 在實作 UI 前建立 MiroFish reuse ledger，以 pinned upstream commit、source path、destination path、reuse mode（verbatim／modified／inspired）、copyright、modification date、適配理由及驗證命令記錄每項引入。
- 不重寫現有 forecasters、ensemble 或 simulation runner。

## 8. 狀態、錯誤與安全

- Empty graph：顯示可執行的 reality-seed starter，不顯示空白 canvas。
- Graph building：逐批 nodes／edges／sources progress；重連後可恢復。
- API error：右側 inline error + retry；graph 保留最後成功 snapshot。
- Simulation engine unavailable：Step 1–2 仍可用，清楚標明 Step 3 受限及 Docker 解法。
- Validation missing：顯示「未驗證」與缺失項，不顯示 `0%` 或中信心。
- Stale async：每次 await 前後校驗 captured graph/session id。
- 所有 timers/WebSocket handlers 在 unmount 清理。
- Report markdown 維持 sanitize；evidence tag 只接受受控 IDs。
- 不在 UI 或 report 暴露模型私有 chain-of-thought。
- Workflow refresh／重新入頁以 server state 恢復；client 不可自行越過 server current step。

## 9. Accessibility、i18n 與視覺約束

- 所有新增 strings 同時加入 `zh-TW.js` 與 `en-US.js`，不得 hardcode。
- Graph 必須提供 keyboard-focusable node list／selected-node textual equivalent。
- 所有 controls 有 visible focus、pressed／selected state、accessible name。
- 支援 Reduce Motion；graph animations 可暫停。
- 顏色不是唯一狀態訊號，credibility tier 同時有文字與 icon／shape。
- 保留 Murmura 黑、白、灰、橙、1px border、低 radius、mono metrics 的 clean-room workbench identity。
- 不引入 cyan glow、glass panels、紫藍漸層或 marketing hero 風格。

## 10. 實作階段

### Phase 0 — Upstream reuse and license gate

固定 MiroFish upstream commit，逐檔比較兩邊 implementation，建立 reuse ledger、third-party attribution 與 Appropriate Legal Notices。只批准有明確功能／時間價值且不降低 Murmura graph、i18n、accessibility、state management 或測試能力的 code reuse。

### Phase A — Scientific truth gate

先修正 fabricated confidence、hardcoded model fit、caller-supplied confidence、generic scenario 誤用香港回測與全域 calibration 問題；建立 fail-closed structured claim／credibility contract 及 backend tests。這是其後 UI 的單一真相來源。

### Phase B — Persistent guided shell

把 backend workflow 設為唯一 source of truth，再拆出 workflow composables／shell，令真實 RAG graph 在五步保持 mounted；加入 Guided/Expert mode、增量 events、resume、desktop/mobile layout 及 Playwright flow tests。

### Phase C — Step integration

逐步把 Step 1–5 接入 persistent graph overlays、meaningful progress、graph evidence drawer 與 Expert sections，同時拆細超大 components。

### Phase D — Trend and evidence experience

把 validation、trend、ensemble、sensitivity、report evidence 接入同一 ScientificEvidenceStrip 與 Step 4 result contract；完成 claim tier、missing-evidence 與 export consistency。

### Phase E — Interaction, visual QA and hardening

完成 Step 5 graph-linked chat/interview/branch comparison、keyboard/mobile/reduced-motion checks、full frontend build、focused backend tests、Playwright journeys、整體 review。

每個 phase 都必須形成可運行、可測試的 vertical slice；不可在未完成 scientific truth gate 前發布新的 confidence UI。

## 11. 測試與驗收

### Backend TDD

- 沒有 ensemble/backtest rows 時，validation response 為 `scenario_exploration`、`confidence_score=null`、列出 missing evidence。
- 只有 ensemble 時最多為 `model_estimate`。
- 只有 consensus 不可提升至 forecast。
- 有符合 domain／metric／horizon 的 backtest 且 beats-naive、calibration evidence 完整時，才可為 `calibrated_forecast`。
- `ConfidenceAssessor` 不再包含硬編碼 `model_fit=0.7`。
- Caller 不可經 query parameter 指定 confidence；LLM 不可生成或升級 credibility tier。
- Generic scenario 不會載入無關的香港宏觀 backtest。
- Report validation summary 必須與目前 claim 的 domain／metric／horizon 對應；否則為 insufficient evidence。
- Models 保持 frozen。

### Frontend TDD／Playwright

- Desktop 由 Step 1 到 Step 5 只有一個 graph renderer instance，step 切換後 camera／selection 保留。
- Step 2、4、5 都可見真實 graph nodes，而不是只見 schematic pulse。
- Guided mode 不顯示 expert controls；toggle 後只顯示當前 step 的 expert section，reload 後模式保留。
- Missing validation 顯示「未驗證」，不顯示假百分比。
- Report evidence click 會選中／聚焦對應 graph node 或 edge。
- Mobile 可在 Step panel 與 graph 間切換並保持 state。
- Loading、empty、error、engine-unavailable、workflow-failed 都有可操作狀態。
- Refresh 或重新進入 workflow 後由 server state 恢復同一步驟及 artifacts；不會因 local `nextStep()` 漂移。
- `npm run typecheck`、`npm run build`、focused Playwright journeys 通過。

### Upstream reuse review

- 直接重用只限於 MiroFish AGPL-covered source，並固定記錄 upstream commit；不可只由 demo bundle、screenshots 或影片反向複製。
- 每個直接重用或修改的檔案都有來源、copyright、license、修改日期及 attribution 紀錄；Murmura `NOTICE`／third-party notices 可追溯所有引入內容。
- 先比較現有 Murmura implementation。若 Murmura graph、state management、accessibility、i18n 或測試能力較成熟，就保留現有 code，只移植較小且有明確價值的 interaction pattern。
- 不直接取用 MiroFish logo、品牌名、screenshots、demo data、未確認授權 assets 或原文產品文案。
- 發佈版保留 AGPL source offer／network-source availability 及 Appropriate Legal Notices。

## 12. 非目標

- 不更換 Vue、FastAPI、D3／force-graph 或 DB stack。
- 不重寫 OASIS simulation engine。
- 不承諾 generic scenario 有真實世界預測能力。
- 不把所有 God View 功能塞入 Guided UI。
- 不以大量動畫、3D、glow 或裝飾取代 evidence clarity。
- 不在本升級加入八字或其他玄學人格來源。
- 不為「看起來更像 MiroFish」而整檔取代 Murmura 已有且功能更完整的 GraphRAG、validation、simulation 或 accessibility implementation。

## 13. 執行與獨立檢視

- Initial architecture 與每個 phase 的 acceptance criteria 由 `gpt-5.6-sol` 規劃。
- 實作遵守 test-first、逐 phase、逐 task review；目前 agent runtime 沒有可選的 `luna 5.6` model，因此不可虛報使用 Luna。實作 agent 使用當前可用執行模型，並在交付紀錄寫明實際 model。
- 每個 phase 完成後由 `gpt-5.6-terra` 做獨立 correctness、scope、scientific-claim、UI regression review；executor self-review 不代替 Terra review。
- 全部 phase 完成後再由 `gpt-5.6-sol` 做 whole-branch final inspection。
- Critical／Important findings 未清零、測試未有 fresh evidence、license/provenance gate 未通過或 upstream reuse review 未完成，都不得宣稱完成。
