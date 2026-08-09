# Guided RAG Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 Murmura 升級成預設最快上手、五步全程保留真實互動式 RAG graph、同時提供 fail-closed 科學驗證與 Expert 路徑的預測工作台。

**Architecture:** Backend workflow 是唯一狀態來源；structured trend claims 與 credibility evidence 先於 LLM narrative 產生。Frontend 只 mount 一個 persistent graph renderer，Step 1–5 只更換右側 task panel 及 graph overlay。MiroFish 合適的 AGPL source 可經逐檔審核後直接修改重用，來源與授權必須可追溯。

**Tech Stack:** FastAPI、Pydantic V2 frozen models、aiosqlite、Vue 3、Vite、vue-i18n、force-graph/D3、Playwright、pytest。

## Global Constraints

- 不加入八字或其他玄學人格來源。
- Guided 是預設；一般用戶每步只有一個主要 CTA，毋須研究設定。
- Expert／Scientific 使用同一 workflow、manifest、session、graph 與 claim contract，不建立第二套 backend path。
- 真實 RAG graph 在 Desktop Step 1–5 持續 mounted；Mobile 每步均可一鍵打開並保留 graph state。
- 無 evidence 必須回傳 `insufficient_evidence`／`null`；不可用 `0.5`、`0.7`、`medium` 或其他中性假值補洞。
- 單次 ABM 最高只可標示 `scenario_exploration`；只有 replicas 可升為 `model_estimate`；只有 domain/metric/horizon 對應 backtest、baseline、calibration 齊全才可升為 `calibrated_forecast`。
- LLM 只可解釋 structured claims，不可生成或修改 direction、estimate、interval、tier、validation status。
- 所有新增 UI strings 使用 `vue-i18n`；新增 controls 有 visible focus、loading、empty、error、keyboard、mobile、Reduce Motion states。
- 所有 user text 經既有 prompt security；report markdown 繼續 sanitize；不公開 private chain-of-thought。
- 所有 workflow/manifest/claim/validation/report 資源都有 owner/workspace authorization；不可只靠可猜 ID。Demo anonymous flow 使用一次性 capability token，不建立公開 mutable endpoint。
- 所有新增／修改 API 使用 `{success, data, meta}` `APIResponse` envelope；錯誤 response 不回傳 `str(exc)`。
- Touched Vue files 不超過 800 lines；`Process.vue` 目標少於 400 lines。
- 不新增 frontend framework 或 design-system dependency。
- MiroFish upstream 固定為 `b5b53acc57189a4a42e44a23e149dc655c98fe82`，實作前重新核對該 commit 仍可取得。
- 直接重用只限已確認為 MiroFish AGPL-covered source；保留 copyright/license notices、上游路徑、commit、修改日期與 source availability。
- 保守合規假設：MiroFish code 是 `AGPL-3.0-only`。若直接引入 derived code，combined distribution metadata 使用 `AGPL-3.0-only`，除非上游另行確認 `or later` grant；既有 Murmura 原創部分仍可保留原 `or later` notice。
- 不直接取用 MiroFish logo、品牌、screenshots、demo data、未確認 assets 或原文產品文案。
- `MiroFish` 名稱只可出現在 legal/upstream attribution surface，不可成為 Murmura product UI brand。
- Luna 執行每個 phase／task 時必須 test-first 並自己檢查 diff；每個完成 phase 交 Terra 獨立 review。Sol 已負責初始架構，只有全部 phase 完成及 Terra clean 後才做 whole-branch final inspection。

---

## File Map

### Source governance

- Create `docs/upstream/mirofish-reuse-audit.md`: pinned upstream、逐檔 reuse 決定、來源與驗證。
- Create `THIRD_PARTY_NOTICES.md`: 實際直接重用後的 notices；沒有直接重用時只記錄「no imported source」。
- Modify `NOTICE`, `README.md`, `package.json`, `frontend/package.json`, `pyproject.toml`: 只有直接重用發生時才收窄 combined distribution metadata 至 `AGPL-3.0-only`。
- Create `frontend/src/views/OpenSourceNotices.vue`: 顯示 source offer、license、upstream notices。

### Scientific truth

- Create `backend/app/services/resource_authorization.py`: owner/workspace/demo-capability gate shared by all new resources。
- Modify `backend/app/models/validation.py`: nullable signals、tier、missing evidence、limitations。
- Create `backend/app/models/experiment_manifest.py`: immutable, versioned experiment contract shared by Guided and Expert。
- Create `backend/app/models/trend_claim.py`: immutable structured claim。
- Create `backend/app/models/claim_assessment.py`, `backend/app/models/validation_evidence.py`: append-only credibility/evidence revisions。
- Create `backend/app/services/experiment_manifest_service.py`: create/freeze/revise manifest lifecycle。
- Create `backend/app/services/recommended_manifest_factory.py`: Guided preview 與 Express autopilot 共用 zero-config frozen manifest factory。
- Modify `backend/app/services/confidence_assessor.py`: 移除假 model fit/baseline。
- Create `backend/app/services/scientific_validation.py`: evidence gate 與 tier promotion。
- Create `backend/app/services/validation_execution_adapter.py`, `validation_worker.py`: durable replicas/backtest/sensitivity execution、recovery、cancel、atomic completion。
- Create `backend/app/services/trend_analysis.py`: 從 simulation artifacts 產生 deterministic claims。
- Create `backend/app/services/trend_claim_repository.py`, `simulation_completion_coordinator.py`: append-only claim persistence 與 mandatory completion hook。
- Modify `backend/app/api/validation.py`: fail-closed response。
- Create `backend/app/api/analysis.py`: claim/credibility/validate endpoints。
- Modify `backend/app/api/simulation_macro.py`: 禁止 caller-supplied confidence。
- Modify `backend/app/services/report_agent.py`: 只讀 session-scoped claim evidence。

### Workflow truth

- Create `backend/app/models/workflow.py`: workflow/event response models。
- Create `backend/app/services/workflow_repository.py`: schema-independent persistence API。
- Create `backend/app/services/workflow_action_service.py`: sole transition entrypoint with durable idempotency receipts。
- Modify `backend/database/schema.sql`, `backend/app/utils/migrations.py`: 正式 workflow schema/migration。
- Modify `backend/app/services/workflow_runner.py`: repository、monotonic events、revision。
- Modify `backend/app/api/workflow.py`: `after_event_id` incremental response。

### Persistent frontend

- Create `frontend/src/api/validation.ts`, `frontend/src/api/analysis.ts`.
- Create `frontend/src/types/workbench.ts`: immutable graph payload/command/overlay contracts shared by every step。
- Create `frontend/tests/e2e/helpers/workbenchMocks.js`: deterministic workflow/graph/validation mocks shared by workbench journeys.
- Create `frontend/src/composables/useWorkflowRun.js`, `usePersistentGraph.js`, `useWorkbenchMode.js`.
- Create `frontend/src/components/workbench/WorkbenchShell.vue`, `WorkbenchHeader.vue`, `WorkflowRail.vue`, `PersistentGraphPane.vue`, `GraphEvidencePanel.vue`, `ScientificLabDrawer.vue`, `ScientificEvidenceStrip.vue`.
- Create focused step components under `frontend/src/components/workbench/steps/`.
- Modify `frontend/src/views/Process.vue` and existing Step 1–5 wrappers to become coordinators/task panels only.

---

## Phase 0 — Upstream reuse and licence gate

### Task 1: Pin and audit MiroFish reuse candidates

**Files:**
- Create: `docs/upstream/mirofish-reuse-audit.md`
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `NOTICE`, `README.md`, `package.json`, `frontend/package.json`, `pyproject.toml` only through the explicit Step 4 branch below

**Interfaces:**
- Consumes: MiroFish commit `b5b53acc57189a4a42e44a23e149dc655c98fe82`; Murmura license files.
- Produces: one auditable decision row per upstream candidate and exact combined-distribution licence state.

- [ ] **Step 1: Verify upstream and both licences**

Run:

```bash
mirofish_audit_dir="$(mktemp -d)"
trap 'test -n "$mirofish_audit_dir" && rm -rf -- "$mirofish_audit_dir"' EXIT
git -C "$mirofish_audit_dir" init
git -C "$mirofish_audit_dir" remote add origin https://github.com/666ghj/MiroFish.git
git -C "$mirofish_audit_dir" fetch --depth 1 origin b5b53acc57189a4a42e44a23e149dc655c98fe82
git -C "$mirofish_audit_dir" cat-file -e 'b5b53acc57189a4a42e44a23e149dc655c98fe82^{commit}'
git -C "$mirofish_audit_dir" show b5b53acc57189a4a42e44a23e149dc655c98fe82:LICENSE | sed -n '1,30p'
for candidate in frontend/src/views/Process.vue frontend/src/components/Step4Report.vue frontend/src/components/Step5Interaction.vue frontend/src/components/GraphPanel.vue; do
  git -C "$mirofish_audit_dir" show "b5b53acc57189a4a42e44a23e149dc655c98fe82:$candidate" | sed -n '1,30p'
done
sed -n '1,24p' LICENSE
rg -n 'AGPL-3.0' README.md package.json frontend/package.json pyproject.toml
```

Expected: the exact pinned commit fetches and resolves as a commit; its own `LICENSE` is GNU AGPL v3; every candidate path exists at that exact commit and any file-level headers are captured; Murmura's local `LICENSE`/metadata is currently AGPL-3.0-or-later. Record the exact commands/output in the ledger. No asset is approved by this audit; any later asset candidate needs its own provenance/licence row before use.

- [ ] **Step 2: Write the reuse ledger with these initial candidate decisions**

The ledger table must include these exact columns:

```markdown
| Upstream path | Destination | Mode | Initial verdict | Reason | Upstream commit | Notice required | Verification |
|---|---|---|---|---|---|---|---|
| frontend/src/components/GraphPanel.vue | frontend/src/components/workbench/PersistentGraphPane.vue | inspired | retain Murmura renderer | Murmura already has temporal snapshots, hulls, contagion, filters and teardown | b5b53acc57189a4a42e44a23e149dc655c98fe82 | no imported code | persistent graph Playwright |
| frontend/src/views/Process.vue | frontend/src/components/workbench/WorkbenchShell.vue | modified excerpts allowed | extract layout only | upstream whole file is monolithic and API-incompatible | b5b53acc57189a4a42e44a23e149dc655c98fe82 | required when copied | typecheck + layout tests |
| frontend/src/components/Step4Report.vue | frontend/src/components/workbench/steps/ReportProgress.vue | modified excerpts allowed | extract collapsible-section/timeline interaction only | upstream interaction is useful but must use Murmura evidence contract | b5b53acc57189a4a42e44a23e149dc655c98fe82 | required when copied | report Playwright |
| frontend/src/components/Step5Interaction.vue | frontend/src/components/workbench/steps/InteractionTargetPicker.vue | modified excerpts allowed | extract target/history interaction only | avoid importing duplicated report pane | b5b53acc57189a4a42e44a23e149dc655c98fe82 | required when copied | interaction Playwright |
```

- [ ] **Step 3: Create attribution rules**

For `WorkbenchShell.vue`, use this exact header when Process excerpts are copied:

```text
<!--
Portions adapted from MiroFish, https://github.com/666ghj/MiroFish
Upstream commit: b5b53acc57189a4a42e44a23e149dc655c98fe82
Upstream path: frontend/src/views/Process.vue
Modified by Murmura contributors on 2026-08-09.
SPDX-License-Identifier: AGPL-3.0-only
-->
```

For `ReportProgress.vue` replace the upstream path line with `frontend/src/components/Step4Report.vue`. For `InteractionTargetPicker.vue` replace it with `frontend/src/components/Step5Interaction.vue`. No other upstream path is approved by this plan without first adding a reviewed ledger row.

If no lines are copied, mark the ledger row `inspired` and do not add a false source header.

- [ ] **Step 4: Set combined distribution metadata only if direct reuse occurs**

If any row is `verbatim` or `modified`, change package/project metadata from `AGPL-3.0-or-later` to `AGPL-3.0-only`, while preserving existing Murmura copyright notices. Add MiroFish source URL, pinned commit and full licence reference to `THIRD_PARTY_NOTICES.md` and `NOTICE`.

If all rows remain `inspired`, leave package licence metadata unchanged and record `No MiroFish source code imported` in the audit.

- [ ] **Step 5: Verify and commit**

Run:

```bash
git diff --check
rg -n 'b5b53acc57189a4a42e44a23e149dc655c98fe82|AGPL-3.0' docs/upstream/mirofish-reuse-audit.md THIRD_PARTY_NOTICES.md NOTICE README.md package.json frontend/package.json pyproject.toml
```

Commit:

```bash
git add docs/upstream/mirofish-reuse-audit.md THIRD_PARTY_NOTICES.md NOTICE README.md package.json frontend/package.json pyproject.toml
git commit -m "docs: record MiroFish reuse provenance"
```

### Task 2: Add open-source notices surface

**Files:**
- Create: `frontend/src/views/OpenSourceNotices.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/i18n/zh-TW.js`
- Modify: `frontend/src/i18n/en-US.js`
- Test: `frontend/tests/e2e/open-source-notices.spec.js`

**Interfaces:**
- Consumes: repository licence and `THIRD_PARTY_NOTICES.md` summary copied as reviewed UI text.
- Produces: `/legal/open-source` route and visible Settings/header link.

- [ ] **Step 1: Write failing Playwright test**

```js
import { expect, test } from '@playwright/test'

test('shows source and third-party notices', async ({ page }) => {
  await page.goto('/legal/open-source')
  await expect(page.getByRole('heading', { name: /開源授權|Open-source licences/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /Source code|源碼/ })).toHaveAttribute('href', /github\.com/)
  await expect(page.getByText(/GNU Affero General Public License/)).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/open-source-notices.spec.js`

Expected: FAIL because `/legal/open-source` does not exist.

- [ ] **Step 3: Implement route and accessible notice view**

The view must use semantic `<main>`, `<h1>`, `<section>` and external source links with visible focus. Do not render licence text through unsanitized HTML.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
cd frontend
npm run typecheck
npx playwright test tests/e2e/open-source-notices.spec.js
```

Commit: `feat: add open-source notices page`

---

## Phase A — Scientific truth gate

### Task 3: Make confidence models fail closed

**Files:**
- Modify: `backend/app/models/validation.py`
- Modify: `backend/app/services/confidence_assessor.py`
- Test: `backend/tests/test_confidence.py`
- Create: `backend/tests/test_confidence_assessor.py`

**Interfaces:**
- Produces: `EvidenceSignal`, `CredibilityTier`, `ConfidenceResult` with nullable score and explicit missing evidence.

- [ ] **Step 1: Write failing model tests**

```python
def test_missing_evidence_has_no_confidence_score() -> None:
    result = ConfidenceResult.insufficient(("backtest", "ensemble"))
    assert result.credibility_tier == "scenario_exploration"
    assert result.confidence_score is None
    assert result.confidence_level == "unverified"
    assert result.missing_evidence == ("backtest", "ensemble")


async def test_assessor_does_not_invent_model_fit(test_db, test_db_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", test_db_path)
    report = await ConfidenceAssessor().assess("session-empty")
    assert report.overall_score is None
    assert report.metrics == ()
    assert "backtest" in report.missing_evidence
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_confidence.py backend/tests/test_confidence_assessor.py -q`

Expected: FAIL because nullable/unverified contracts do not exist and assessor invents a score.

- [ ] **Step 3: Implement immutable types**

Use these exact public types:

```python
CredibilityTier = Literal["scenario_exploration", "model_estimate", "calibrated_forecast"]
EvidenceStatus = Literal["available", "partial", "missing"]
ConfidenceLevel = Literal["high", "medium", "low", "unverified"]

class EvidenceSignal(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    status: EvidenceStatus
    value: float | None = None
    source_id: str | None = None

class ConfidenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    credibility_tier: CredibilityTier
    confidence_level: ConfidenceLevel
    confidence_score: float | None
    signals: tuple[EvidenceSignal, ...]
    missing_evidence: tuple[str, ...]
    limitations: tuple[str, ...]

    @classmethod
    def insufficient(cls, missing: tuple[str, ...]) -> "ConfidenceResult":
        return cls(
            credibility_tier="scenario_exploration",
            confidence_level="unverified",
            confidence_score=None,
            signals=tuple(EvidenceSignal(name=name, status="missing") for name in missing),
            missing_evidence=missing,
            limitations=("此結果只可作情景探索",),
        )
```

Delete the hardcoded `model_fit=0.7` and the no-decisions baseline formula. Keep compatibility fields only if they remain nullable and documented deprecated.

`confidence_score` and `confidence_level` are deprecated compatibility fields, not a new composite scientific score. For every claim-scoped `scenario_exploration`, `model_estimate`, and `calibrated_forecast` response in this plan, return `confidence_score=None` and `confidence_level="unverified"`; consumers use `credibility_tier`, estimate/interval, MCSE, proper losses, coverage and missing-evidence fields directly. Do not map tiers to percentages or high/medium/low labels. A future numeric score requires a separate versioned calibration study and is outside this plan.

- [ ] **Step 4: Verify GREEN and regression suite**

Run:

```bash
.venv311/bin/python -m pytest backend/tests/test_confidence.py backend/tests/test_confidence_assessor.py backend/tests/test_universal_engine_integration.py -q
```

- [ ] **Step 5: Commit**

Commit: `fix: make confidence assessment fail closed`

### Task 4: Add immutable versioned experiment manifests

**Files:**
- Create: `backend/app/models/experiment_manifest.py`
- Create: `backend/app/services/simulation_config_adapter.py`
- Create: `backend/app/services/resource_authorization.py`
- Create: `backend/app/services/experiment_manifest_service.py`
- Create: `backend/app/services/recommended_manifest_factory.py`
- Create: `backend/app/api/manifests.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/database/schema.sql`
- Modify: `backend/app/utils/migrations.py`
- Create: `backend/tests/test_experiment_manifest.py`
- Create: `backend/tests/api/test_manifests_api.py`
- Create: `backend/tests/api/test_resource_authorization.py`
- Create: `backend/tests/helpers/manifest_fixtures.py`

**Interfaces:**
- Produces: `ExperimentManifest`, `ManifestStatus`, create/update/freeze/revise lifecycle, `POST /api/manifests`, `GET /api/manifests/{manifest_id}`, `PATCH /api/manifests/{manifest_id}`, `POST /api/manifests/{manifest_id}/freeze`, `POST /api/manifests/{manifest_id}/revisions`.
- Produces `RecommendedManifestFactory.create_draft(*, workflow_id: str, graph_id: str, graph_revision: int, domain_pack_id: str, preset: str) -> ExperimentManifest` and idempotent `create_and_freeze(...) -> ExperimentManifest`; the service resolves `workflow_id` to its immutable root, persists that as `root_workflow_id`, and records the requesting branch as `authored_from_workflow_id`. `POST /api/manifests/recommended` exposes the draft method for Guided preview, while Express uses the same draft then freezes it server-side.
- Produces `SimulationConfigAdapter.from_manifest(manifest: ExperimentManifest, graph_id: str, graph_revision: int) -> SimulationCreateRequest`; `graph_id` and `graph_revision` come from the server-loaded workflow graph snapshot, must exactly equal the frozen manifest pins, and are never accepted as action-body overrides. `start_simulation` accepts no unversioned simulation overrides and uses this adapter exclusively.
- All manifest endpoints resolve `ResourcePrincipal` and call `ResourceAuthorization.require_read()`/`require_write()` against the owning workflow before returning or mutating data.
- Later tasks store `manifest_id` on workflow, session, validation evidence and every trend claim.
- Test helper produces `manifest_input()` and `frozen_manifest()` with the exact public-narrative fixture shown below; Tasks 5–7 import it instead of redefining manifest data.

- [ ] **Step 1: Write failing lifecycle tests**

```python
def manifest_input() -> dict:
    return {
        "workflow_id": "workflow-1",
        "graph_id": "graph-7",
        "graph_revision": 3,
        "domain": "public_narrative",
        "metrics": [{"name": "support", "forecast_kind": "probability"}],
        "horizon": "20_rounds",
        "population_spec": {"target_count": 300, "source": "kg"},
        "simulation_config": {
            "schema_version": "simulation-config-v1", "scenario_type": "public_narrative",
            "preset_name": "standard", "agent_count": 300, "round_count": 20, "mc_trials": 50,
            "agent_distribution": [],
            "platforms": [{"name": "twitter", "enabled": True}, {"name": "reddit", "enabled": True}],
            "shocks": [], "domain_pack_id": "public_narrative", "macro_scenario_id": None,
            "company_count": 0, "llm_provider": "openrouter", "llm_model": "deepseek-v3.2",
            "llm_model_lite": "deepseek-v3.2-lite", "llm_base_url": None,
            "credential_profile_id": "credential-default", "cost_budget_usd": 3.0,
            "input_dataset_pins": [],
        },
        "model_versions": [{"name": "agents", "version": "deepseek-v3.2"}],
        "data_versions": [{"name": "graph", "version": "graph-7@revision-3"}],
        "rule_versions": [{"name": "activation", "version": "temporal-v1"}],
        "random_seeds": [101, 202, 303, 404, 505, 606, 707, 808],
        "replica_strategy": {"mode": "fixed", "min_replicas": 8, "max_replicas": 8,
                             "seed_policy": "fixed_set", "relative_mcse_threshold": 0.05},
        "backtest_config": {"method": "walk_forward", "min_folds": 3,
                            "min_observations": 30, "baseline": "naive"},
        "calibration_config": {"min_samples": 30, "probability_bins": 10,
                               "interval_levels": [0.8, 0.95], "coverage_tolerance": 0.05},
        "sensitivity_config": {"enabled": True, "method": "sobol", "sample_count": 512},
    }


def frozen_manifest() -> ExperimentManifest:
    return ExperimentManifest(
        manifest_id="manifest-1",
        root_workflow_id="workflow-1",
        authored_from_workflow_id="workflow-1",
        graph_id="graph-7",
        graph_revision=3,
        recommendation_key="recommendation:workflow-1:graph-7:3:public_narrative:standard:v1",
        revision=1,
        status="frozen",
        domain="public_narrative",
        metrics=(MetricSpec(name="support", forecast_kind="probability"),),
        horizon="20_rounds",
        population_spec=PopulationSpec(target_count=300, source="kg"),
        simulation_config=simulation_config_snapshot(),
        model_versions=(VersionPin(name="agents", version="deepseek-v3.2"),),
        data_versions=(VersionPin(name="graph", version="graph-7@revision-3"),),
        rule_versions=(VersionPin(name="activation", version="temporal-v1"),),
        random_seeds=(101, 202, 303, 404, 505, 606, 707, 808),
        planned_seed_set_hash=canonical_seed_hash((101, 202, 303, 404, 505, 606, 707, 808)),
        manifest_hash=canonical_manifest_hash(frozen_manifest_payload()),
        replica_strategy=ReplicaStrategy(mode="fixed", min_replicas=8, max_replicas=8,
                                         seed_policy="fixed_set", relative_mcse_threshold=0.05),
        backtest_config=BacktestConfig(method="walk_forward", min_folds=3,
                                       min_observations=30, baseline="naive"),
        calibration_config=CalibrationConfig(min_samples=30, probability_bins=10,
                                             interval_levels=(0.8, 0.95), coverage_tolerance=0.05),
        sensitivity_config=SensitivityConfig(enabled=True, method="sobol", sample_count=512),
        created_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        frozen_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
    )


async def test_frozen_manifest_cannot_be_mutated(service) -> None:
    draft = await service.create(manifest_input())
    frozen = await service.freeze(draft.manifest_id)
    assert frozen.status == "frozen"
    with pytest.raises(FrozenManifestError):
        await service.update(
            frozen.manifest_id,
            {"model_versions": [{"name": "agents", "version": "deepseek-v3.3"}]},
        )


async def test_revision_preserves_parent_and_increments_version(service) -> None:
    frozen = await service.freeze((await service.create(manifest_input())).manifest_id)
    revised = await service.revise(
        frozen.manifest_id,
        {"model_versions": [{"name": "agents", "version": "deepseek-v3.3"}]},
    )
    assert revised.parent_manifest_id == frozen.manifest_id
    assert revised.revision == frozen.revision + 1
    assert revised.status == "draft"


@pytest.mark.parametrize(
    "changes",
    [
        {"replica_strategy": {"mode": "fixed", "min_replicas": 9, "max_replicas": 8,
                              "seed_policy": "fixed_set", "relative_mcse_threshold": 0.05}},
        {"random_seeds": [101, 202]},
        {"calibration_config": {"min_samples": 30, "probability_bins": 10,
                                "interval_levels": [0.0, 0.95], "coverage_tolerance": 0.05}},
    ],
)
def test_manifest_rejects_incoherent_scientific_config(changes) -> None:
    values = manifest_input()
    values.update(changes)
    with pytest.raises(ValidationError):
        ExperimentManifestCreate(**values)


def test_frozen_manifest_has_no_nested_mutable_containers() -> None:
    manifest = frozen_manifest()
    with pytest.raises(ValidationError):
        manifest.population_spec.target_count = 999
    with pytest.raises(TypeError):
        manifest.model_versions[0] = VersionPin(name="agents", version="other")


async def test_recommended_factory_returns_workflow_owned_frozen_manifest(recommended_factory) -> None:
    manifest = await recommended_factory.create_and_freeze(
        workflow_id="workflow-1", graph_id="graph-7", graph_revision=3,
        domain_pack_id="public_narrative", preset="standard",
    )
    assert manifest.root_workflow_id == "workflow-1"
    assert manifest.authored_from_workflow_id == "workflow-1"
    assert manifest.status == "frozen"
    assert manifest.population_spec.target_count == 300
    assert len(manifest.random_seeds) == manifest.replica_strategy.max_replicas


async def test_recommended_factory_reuses_same_manifest_across_crash_boundaries(recommended_factory) -> None:
    kwargs = {
        "workflow_id": "workflow-1", "graph_id": "graph-7", "graph_revision": 3,
        "domain_pack_id": "public_narrative", "preset": "standard",
    }
    draft = await recommended_factory.create_draft(**kwargs)
    same_draft = await recommended_factory.create_draft(**kwargs)
    frozen = await recommended_factory.create_and_freeze(**kwargs)
    after_restart = await RecommendedManifestFactory(recommended_factory.db_path).create_and_freeze(**kwargs)
    assert same_draft.manifest_id == draft.manifest_id
    assert frozen.manifest_id == draft.manifest_id
    assert after_restart.manifest_id == draft.manifest_id
    assert after_restart.status == "frozen"


def test_simulation_request_comes_only_from_frozen_snapshot(monkeypatch, config_adapter) -> None:
    monkeypatch.setenv("AGENT_LLM_MODEL", "must-not-leak")
    manifest = frozen_manifest()
    request = config_adapter.from_manifest(manifest, graph_id="graph-7", graph_revision=3)
    assert request.agent_count == manifest.simulation_config.agent_count
    assert request.round_count == manifest.simulation_config.round_count
    assert request.llm_model == manifest.simulation_config.llm_model
    assert request.llm_model != "must-not-leak"
    assert request.shocks == []


@pytest.mark.parametrize(
    ("graph_id", "graph_revision"),
    [("graph-other", 3), ("graph-7", 4)],
)
def test_simulation_adapter_rejects_graph_pin_mismatch_without_building_request(
    config_adapter, graph_id, graph_revision
) -> None:
    with pytest.raises(ManifestGraphMismatch):
        config_adapter.from_manifest(
            frozen_manifest(), graph_id=graph_id, graph_revision=graph_revision
        )
    assert config_adapter.requests_built == 0


async def test_cross_workspace_manifest_access_is_hidden(test_client, workspace_a_manifest, user_b_token) -> None:
    response = await test_client.get(
        f"/api/manifests/{workspace_a_manifest.manifest_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert response.status_code == 404


async def test_workspace_viewer_cannot_freeze_manifest(test_client, draft_manifest, viewer_token) -> None:
    response = await test_client.post(
        f"/api/manifests/{draft_manifest.manifest_id}/freeze",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_experiment_manifest.py backend/tests/api/test_manifests_api.py backend/tests/api/test_resource_authorization.py -q`

Expected: FAIL because manifest model/service/routes do not exist.

- [ ] **Step 3: Implement immutable contract and persistence**

```python
ManifestStatus = Literal["draft", "frozen", "superseded"]

class PopulationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    target_count: int
    source: Literal["kg", "census", "generated"]

class VersionPin(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    version: str

class MetricSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    forecast_kind: Literal["probability", "continuous"]

class PlatformSelection(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    enabled: bool

class DistributionEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    key: str
    share: float

class CanonicalJsonPin(BaseModel):
    model_config = ConfigDict(frozen=True)
    canonical_json: str
    sha256: str

class ShockSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    round_number: int
    shock_type: str
    description: str
    post_content: str
    parameters: CanonicalJsonPin
    macro_effects: CanonicalJsonPin | None

class InputDatasetPin(BaseModel):
    model_config = ConfigDict(frozen=True)
    dataset_id: str
    kind: Literal["family_members", "crm", "uploaded_population"]
    sha256: str

class SimulationConfigSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    schema_version: Literal["simulation-config-v1"]
    scenario_type: str
    preset_name: Literal["fast", "standard", "deep", "large", "massive", "custom"]
    agent_count: int
    round_count: int
    mc_trials: int
    agent_distribution: tuple[DistributionEntry, ...]
    platforms: tuple[PlatformSelection, ...]
    shocks: tuple[ShockSnapshot, ...]
    hook_config: HookConfig
    domain_pack_id: str
    macro_scenario_id: str | None
    company_count: int
    llm_provider: str
    llm_model: str
    llm_model_lite: str | None
    llm_base_url: str | None
    credential_profile_id: str | None
    cost_budget_usd: float
    input_dataset_pins: tuple[InputDatasetPin, ...]

class ReplicaStrategy(BaseModel):
    model_config = ConfigDict(frozen=True)
    mode: Literal["fixed", "sequential"]
    min_replicas: int
    max_replicas: int
    seed_policy: Literal["fixed_set"]
    relative_mcse_threshold: float

class BacktestConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    method: Literal["walk_forward"]
    min_folds: int
    min_observations: int
    baseline: Literal["naive"]

class CalibrationConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    min_samples: int
    probability_bins: int
    interval_levels: tuple[float, ...]
    coverage_tolerance: float

class SensitivityConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    enabled: bool
    method: Literal["sobol"]
    sample_count: int

class ExperimentManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    manifest_id: str
    root_workflow_id: str
    authored_from_workflow_id: str
    graph_id: str
    graph_revision: int
    recommendation_key: str | None = None
    parent_manifest_id: str | None = None
    revision: int
    status: ManifestStatus
    domain: str
    metrics: tuple[MetricSpec, ...]
    horizon: str
    population_spec: PopulationSpec
    simulation_config: SimulationConfigSnapshot
    model_versions: tuple[VersionPin, ...]
    data_versions: tuple[VersionPin, ...]
    rule_versions: tuple[VersionPin, ...]
    random_seeds: tuple[int, ...]
    planned_seed_set_hash: str
    manifest_hash: str
    replica_strategy: ReplicaStrategy
    backtest_config: BacktestConfig
    calibration_config: CalibrationConfig
    sensitivity_config: SensitivityConfig
    created_at: datetime
    frozen_at: datetime | None = None
```

Add Pydantic cross-field validators with these exact invariants: non-empty `graph_id` and positive `graph_revision`; at least one metric with unique names and explicit forecast kind; simulation agent count equals population target; round/agent/mc limits match `resolve_preset`/custom bounds; distribution shares are unique and sum to 1 within `1e-9` when supplied; platform names are unique with at least one enabled; shock rounds lie within `1..round_count`; canonical JSON and dataset hashes verify; cost budget is positive; provider/model identifiers are non-empty; no raw API key is allowed. Snapshot every field of the existing frozen `HookConfig` dataclass, including scaled values, rather than recomputing hooks at execution. Also enforce `1 <= min_replicas <= max_replicas`; `fixed` requires `min_replicas == max_replicas == len(random_seeds)`; `sequential` requires `len(random_seeds) == max_replicas` and consumes only a deterministic prefix; seeds are unique; `0 < relative_mcse_threshold <= 1`; `min_folds >= 3`; `min_observations >= 30`; `min_samples >= 30`; `probability_bins >= 2`; interval levels are unique and each lies strictly within `(0, 1)`; `0 < coverage_tolerance < 0.5`; enabled Sobol sensitivity requires a power-of-two `sample_count >= 128`.

Canonicalize the complete manifest excluding `manifest_hash`, explicitly including `graph_id`, `graph_revision`, and the serialized `SimulationConfigSnapshot`/`HookConfig`, and compute `manifest_hash` server-side after every draft create/patch/revision; freeze re-verifies it and never accepts caller hashes. Manifest create/recommend/revise services load the workflow's persisted graph snapshot server-side and populate graph pins; request bodies cannot choose or override them. `SimulationConfigAdapter` verifies the manifest hash and exact equality with the server-loaded workflow `graph_id` plus `graph_revision`, loads only dataset rows whose IDs/hashes match pins, resolves the workspace-owned credential reference without persisting secrets, and only then constructs `SimulationCreateRequest` with the exact snapshot. It may not call `HookConfig.scaled()`, `resolve_preset()`, environment model defaults or accept endpoint overrides during execution. Persist `manifest_id`, `manifest_hash`, `graph_id`, and `graph_revision` on the simulation session/job for attestation.

`ResourceAuthorization` uses existing `get_current_user`/workspace membership for authenticated calls. Personal resources require exact `owner_user_id`; workspace reads allow `viewer|editor|admin|owner`, while create/freeze/revise/start/cancel/retry/validate require `editor|admin|owner`. Every workflow and child table stores `owner_user_id`, nullable `workspace_id`, and `root_workflow_id`; child authorization resolves the root instead of trusting request-supplied ownership. Manifest authorization uses `root_workflow_id`; `authored_from_workflow_id` is provenance only and must resolve to that same root. Missing or unauthorized read returns the same 404; an authenticated member with read access but insufficient mutation role gets 403. In `DEMO_MODE` only, draft creation may issue a 256-bit workflow capability once, store only its hash, and require `X-Workflow-Token` for every anonymous child read/write; frontend keeps it in `sessionStorage`, never URL/localStorage/logs. Production anonymous mutation returns 401. Existing report share token remains a separate read-only pinned-report capability.

Create `experiment_manifests` with `root_workflow_id`, `authored_from_workflow_id`, unique `(root_workflow_id, revision)`, immutable frozen rows, JSON text for tuple submodels/seeds, and `parent_manifest_id` self-reference. Recommended rows also store `recommendation_key`, unique across `(root_workflow_id, graph_id, graph_revision, domain_pack_id, preset, recommendation_factory_version)`. A revision request from a child branch keeps the same root, records that child as authoring provenance, and requires its `parent_manifest_id` lineage to resolve within the same root and graph. The later simulation session stores `manifest_id` and `manifest_hash`; a frozen manifest is never mutated to attach a session. API uses `APIResponse`; revisions never overwrite the frozen parent.

`RecommendedManifestFactory` calls existing `ZeroConfigService`/domain-pack and preset resolution, resolves the supplied workflow to `root_workflow_id`, pins the resolved model/data/rule versions, derives deterministic unique seeds from `root_workflow_id + graph revision`, validates the full contract, and transactionally get-or-creates by `recommendation_key`. `create_draft` returns the existing draft/frozen row; `create_and_freeze` freezes that same row exactly once and returns it if already frozen. It never starts a simulation. `fast|standard|deep|large|massive` map through existing preset counts; validation defaults remain explicitly present in the manifest. Crash after draft create, after freeze, or before workflow manifest linkage therefore reuses the same `manifest_id`; the workflow runner test injects each boundary. The same factory result is shown to Guided users before they accept Step 2 and is created server-side after graph completion for Express autopilot.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
.venv311/bin/python -m pytest backend/tests/test_experiment_manifest.py backend/tests/api/test_manifests_api.py backend/tests/api/test_resource_authorization.py -q
```

Commit: `feat: add versioned experiment manifests`

### Task 5: Gate credibility promotion on real evidence

**Files:**
- Create: `backend/app/models/validation_evidence.py`
- Create: `backend/app/services/scientific_validation.py`
- Create: `backend/app/services/validation_evidence_repository.py`
- Modify: `backend/app/api/validation.py`
- Modify: `backend/database/schema.sql`
- Modify: `backend/app/utils/migrations.py`
- Create: `backend/tests/test_scientific_validation.py`
- Create: `backend/tests/api/test_validation_api.py`

**Interfaces:**
- Consumes: one frozen `ExperimentManifest`, one claim scope `(manifest_id, domain, metric, horizon, forecast_kind)`, and claim-scoped `ValidationEvidence`.
- Produces: `ScientificValidationService.assess_scope(manifest: ExperimentManifest, scope: ClaimScope) -> ConfidenceResult`; Task 6 binds persisted claim IDs to this scope.
- Produces pure helper: `assess_evidence(*, manifest: ExperimentManifest, scope: ClaimScope, evidence: ValidationEvidence | None) -> ConfidenceResult`.

- [ ] **Step 1: Write failing promotion matrix tests**

```python
@pytest.fixture
def manifest() -> ExperimentManifest:
    return frozen_manifest()


@pytest.fixture
def claim_scope() -> ClaimScope:
    return ClaimScope(
        claim_id="claim-1",
        manifest_id="manifest-1",
        domain="public_narrative",
        metric="support",
        horizon="20_rounds",
        forecast_kind="probability",
    )


def valid_evidence(**changes) -> ValidationEvidence:
    values = {
        "evidence_id": "evidence-1",
        "validation_job_id": "validation-job-1",
        "evidence_revision": 1,
        "claim_id": "claim-1",
        "manifest_id": "manifest-1",
        "domain": "public_narrative",
        "metric": "support",
        "horizon": "20_rounds",
        "forecast_kind": "probability",
        "executed_seeds": (101, 202, 303, 404, 505, 606, 707, 808),
        "planned_seed_set_hash": canonical_seed_hash((101, 202, 303, 404, 505, 606, 707, 808)),
        "executed_seed_prefix_hash": canonical_seed_hash((101, 202, 303, 404, 505, 606, 707, 808)),
        "requested_replicas": 8,
        "completed_replicas": 8,
        "completion_rate": 1.0,
        "relative_mcse": 0.03,
        "stable": True,
        "fold_ids": ("fold-1", "fold-2", "fold-3"),
        "folds_are_scoped": True,
        "observation_period": ("2024-01-01", "2026-01-01"),
        "observation_count": 40,
        "score_type": "brier",
        "model_score": 0.16,
        "baseline_score": 0.23,
        "calibration_sample_size": 40,
        "estimate": 0.63,
        "prediction_interval": (0.55, 0.71),
        "interval_level": None,
        "observed_coverage": None,
        "provenance_ids": ("obs-dataset-7", "backtest-run-9"),
        "created_at": datetime(2026, 8, 9, tzinfo=timezone.utc),
    }
    values.update(changes)
    return ValidationEvidence(**values)


def test_complete_matching_evidence_promotes_to_calibrated(manifest, claim_scope) -> None:
    result = assess_evidence(manifest=manifest, scope=claim_scope, evidence=valid_evidence())
    assert result.credibility_tier == "calibrated_forecast"


@pytest.mark.parametrize(
    "changes",
    [
        {"metric": "awareness"},
        {"horizon": "10_rounds"},
        {"manifest_id": "manifest-other"},
        {"completed_replicas": 6, "completion_rate": 0.75},
        {"relative_mcse": 0.09},
        {"stable": False},
        {"folds_are_scoped": False},
        {"score_type": "crps"},
        {"model_score": 0.25, "baseline_score": 0.23},
        {"observation_count": 20, "calibration_sample_size": 20},
        {"provenance_ids": ()},
        {"requested_replicas": 9},
        {"completed_replicas": 9},
        {"completed_replicas": 7, "completion_rate": 1.0},
        {"executed_seeds": (808, 707, 606, 505, 404, 303, 202, 101)},
        {"planned_seed_set_hash": "sha256:wrong-plan"},
        {"executed_seed_prefix_hash": "sha256:wrong-prefix"},
    ],
)
def test_mismatch_or_incomplete_evidence_cannot_be_calibrated(manifest, claim_scope, changes) -> None:
    result = assess_evidence(manifest=manifest, scope=claim_scope, evidence=valid_evidence(**changes))
    assert result.credibility_tier != "calibrated_forecast"


def test_replicas_without_backtest_are_only_model_estimate(manifest, claim_scope) -> None:
    evidence = valid_evidence(fold_ids=(), observation_count=0, score_type=None, model_score=None,
                              baseline_score=None, calibration_sample_size=0)
    result = assess_evidence(manifest=manifest, scope=claim_scope, evidence=evidence)
    assert result.credibility_tier == "model_estimate"


def test_continuous_forecast_requires_interval_coverage(manifest) -> None:
    scope = ClaimScope(
        claim_id="claim-2", manifest_id="manifest-1", domain="public_narrative",
        metric="support", horizon="20_rounds", forecast_kind="continuous",
    )
    evidence = valid_evidence(
        evidence_id="evidence-2", claim_id="claim-2", forecast_kind="continuous",
        score_type="crps", interval_level=0.8, observed_coverage=0.61,
    )
    result = assess_evidence(manifest=manifest, scope=scope, evidence=evidence)
    assert result.credibility_tier != "calibrated_forecast"


async def test_evidence_history_survives_service_restart(evidence_repository) -> None:
    first = await evidence_repository.append(valid_evidence())
    restarted = ValidationEvidenceRepository(evidence_repository.db_path)
    assert (await restarted.get(first.evidence_id)) == first
    assert (await restarted.latest_for_claim("claim-1")).evidence_revision == 1
```

Add API test asserting an empty session returns `confidence_score: null`, never fabricated MC/Theil defaults.

```python
async def test_empty_session_validation_is_unverified(test_client) -> None:
    response = await test_client.get("/api/validation/session-empty")
    assert response.status_code == 200
    envelope = response.json()
    assert envelope["success"] is True
    payload = envelope["data"]
    assert payload["credibility_tier"] == "scenario_exploration"
    assert payload["confidence_score"] is None
    assert set(payload["missing_evidence"]) >= {"backtest", "ensemble"}
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_scientific_validation.py backend/tests/api/test_validation_api.py -q`

- [ ] **Step 3: Implement service and thin router**

Implement this frozen evidence contract:

```python
class ClaimScope(BaseModel):
    model_config = ConfigDict(frozen=True)
    claim_id: str
    manifest_id: str
    domain: str
    metric: str
    horizon: str
    forecast_kind: Literal["probability", "continuous"]


class ValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    evidence_id: str
    validation_job_id: str
    evidence_revision: int
    claim_id: str
    manifest_id: str
    domain: str
    metric: str
    horizon: str
    forecast_kind: Literal["probability", "continuous"]
    executed_seeds: tuple[int, ...]
    planned_seed_set_hash: str
    executed_seed_prefix_hash: str
    requested_replicas: int
    completed_replicas: int
    completion_rate: float
    relative_mcse: float | None
    stable: bool
    fold_ids: tuple[str, ...]
    folds_are_scoped: bool
    observation_period: tuple[str, str] | None
    observation_count: int
    score_type: Literal["brier", "log_loss", "crps"] | None
    model_score: float | None
    baseline_score: float | None
    calibration_sample_size: int
    estimate: float | None
    prediction_interval: tuple[float, float] | None
    interval_level: float | None
    observed_coverage: float | None
    provenance_ids: tuple[str, ...]
    created_at: datetime
```

`model_estimate` requires a frozen matching manifest, `requested_replicas` within the manifest min/max, `completed_replicas <= requested_replicas`, completion rate equal to `completed/requested` within `1e-9` and ≥0.90, and `executed_seeds` equal to the exact manifest seed prefix of length `requested_replicas`. Evidence `planned_seed_set_hash` must equal the hash of all manifest seeds, while `executed_seed_prefix_hash` must equal the canonical hash of exactly `executed_seeds`; these are distinct for an early-stopped sequential run. It also requires `stable=True` and `relative_mcse <= manifest.replica_strategy.relative_mcse_threshold`. Fixed strategy requires the full seed set; sequential strategy may stop only after its minimum and uses no unplanned seed. `calibrated_forecast` additionally requires exact manifest/domain/metric/horizon/forecast-kind match, at least `manifest.backtest_config.min_folds` fold-scoped out-of-sample folds, observation count and calibration sample size at least their manifest thresholds, non-empty observation period/provenance, proper loss (`brier|log_loss` for probability, `crps` for continuous), and `model_score < baseline_score`; every stored score is a loss to minimize. A continuous forecast also requires `interval_level` to be declared in `manifest.calibration_config.interval_levels` and `abs(observed_coverage - interval_level) <= manifest.calibration_config.coverage_tolerance`; probability evidence leaves both interval fields null. Any mismatch returns a machine-readable missing/rejection reason. The router must never substitute absent rows. `agent_consensus` may populate a signal but cannot promote a claim.

Persist evidence in an append-only `validation_evidence` table. Use `evidence_id` as the primary key, unique `(claim_id, evidence_revision)`, and indexes on `validation_job_id` and `claim_id`. A validation job allocates the next revision for each claim in one transaction; evidence rows are never updated. The repository exposes exact lookup by `evidence_id`, ordered history, and latest-by-highest-revision lookup so a process restart cannot lose or silently replace scientific evidence.

- [ ] **Step 4: Verify GREEN and commit**

Run: `.venv311/bin/python -m pytest backend/tests/test_scientific_validation.py backend/tests/api/test_validation_api.py backend/tests/test_validation_suite.py -q`

Commit: `feat: gate credibility on session evidence`

### Task 6: Add immutable structured trend claims

**Files:**
- Create: `backend/app/models/trend_claim.py`
- Create: `backend/app/models/claim_assessment.py`
- Create: `backend/app/services/trend_analysis.py`
- Create: `backend/app/services/trend_claim_repository.py`
- Create: `backend/app/services/simulation_completion_coordinator.py`
- Create: `backend/app/services/validation_execution_adapter.py`
- Create: `backend/app/services/validation_worker.py`
- Modify: `backend/app/services/simulation_worker.py`
- Create: `backend/app/api/analysis.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/database/schema.sql`
- Modify: `backend/app/utils/migrations.py`
- Create: `backend/tests/test_trend_analysis.py`
- Create: `backend/tests/test_validation_worker.py`
- Test: `backend/tests/test_simulation_worker.py`
- Create: `backend/tests/api/test_analysis_api.py`

**Interfaces:**
- Produces immutable base facts with `build_claim(*, session_id: str, manifest: ExperimentManifest, metric: str, forecast_kind: Literal["probability", "continuous"], horizon: str, values: tuple[float, ...], evidence_ids: tuple[str, ...], counter_signals: tuple[str, ...]) -> TrendClaim`.
- Produces append-only assessment history with `build_initial_assessment(claim_id: str) -> ClaimAssessment`, `append_validation_assessment(claim_id: str, validation_job_id: str, result: ConfidenceResult, evidence: ValidationEvidence) -> ClaimAssessment`, and `project_claim(claim: TrendClaim, latest: ClaimAssessment) -> TrendClaimView`.
- Produces `SimulationCompletionCoordinator.finalize(session_id: str, simulation_job_id: int, manifest_id: str) -> tuple[TrendClaim, ...]`, the mandatory simulation-completion hook that persists base claims before a session is exposed as completed.
- Produces `GET /api/analysis/{session_id}/claims`, `GET /api/analysis/{session_id}/claims/{claim_id}/assessments`, `GET /api/analysis/{session_id}/credibility`, `POST /api/analysis/{session_id}/validate`, `GET /api/analysis/{session_id}/validation-jobs/{job_id}`, and `POST /api/analysis/{session_id}/validation-jobs/{job_id}/cancel`.
- `POST /validate` requires `Idempotency-Key` and frozen `manifest_id`; body is `{"manifest_id": str, "claim_ids": list[str], "mode": "safe_auto"|"scientific"}`. It returns HTTP 202 with `validation_job_id` and `queued` unless the same key already has a result.

- [ ] **Step 1: Write failing deterministic claim tests**

```python
def test_single_run_claim_is_scenario_only() -> None:
    claim = build_claim(
        session_id="session-1",
        manifest=frozen_manifest(),
        metric="support",
        forecast_kind="probability",
        horizon="20_rounds",
        values=(0.41, 0.46, 0.49),
        evidence_ids=("action-1", "action-2"),
        counter_signals=("opposition rose in round 18",),
    )
    assessment = build_initial_assessment(claim.claim_id)
    view = project_claim(claim, assessment)
    assert claim.session_id == "session-1"
    assert claim.manifest_id == "manifest-1"
    assert claim.horizon == "20_rounds"
    assert claim.forecast_kind == "probability"
    assert claim.evidence_ids == ("action-1", "action-2")
    assert claim.direction == "up"
    assert view.credibility_tier == "scenario_exploration"
    assert view.validation_status == "insufficient_evidence"
    assert view.estimate is None


def test_llm_fields_are_not_part_of_claim_input() -> None:
    assert "narrative" not in TrendClaim.model_fields
    assert "credibility_tier" not in TrendClaim.model_fields
    assert TrendClaim.model_config["frozen"] is True


async def test_validation_appends_assessment_without_mutating_claim(repository, persisted_claim, validated_evidence) -> None:
    before = await repository.get_claim(persisted_claim.claim_id)
    result = ConfidenceResult(
        credibility_tier="calibrated_forecast", confidence_level="unverified", confidence_score=None,
        signals=(), missing_evidence=(), limitations=(),
    )
    assessment = await repository.append_validation_assessment(
        persisted_claim.claim_id, "validation-job-2", result, validated_evidence
    )
    after = await repository.get_claim(persisted_claim.claim_id)
    history = await repository.list_assessments(persisted_claim.claim_id)
    assert after == before
    assert assessment.revision == 2
    assert [item.revision for item in history] == [1, 2]
    assert (await repository.get_claim_view(persisted_claim.claim_id)).credibility_tier == "calibrated_forecast"


async def test_validation_job_rejects_manifest_mismatch(test_client, persisted_claim) -> None:
    response = await test_client.post(
        f"/api/analysis/{persisted_claim.session_id}/validate",
        headers={"Idempotency-Key": "validate-1"},
        json={"manifest_id": "manifest-other", "claim_ids": [persisted_claim.claim_id], "mode": "safe_auto"},
    )
    assert response.status_code == 409


async def test_validation_job_is_idempotent(test_client, persisted_claim) -> None:
    body = {"manifest_id": persisted_claim.manifest_id, "claim_ids": [persisted_claim.claim_id], "mode": "safe_auto"}
    first = await test_client.post(
        f"/api/analysis/{persisted_claim.session_id}/validate",
        headers={"Idempotency-Key": "validate-same"},
        json=body,
    )
    second = await test_client.post(
        f"/api/analysis/{persisted_claim.session_id}/validate",
        headers={"Idempotency-Key": "validate-same"},
        json=body,
    )
    assert first.status_code == second.status_code == 202
    assert first.json()["data"]["validation_job_id"] == second.json()["data"]["validation_job_id"]


async def test_validation_key_reuse_with_different_request_is_conflict(test_client, persisted_claim) -> None:
    endpoint = f"/api/analysis/{persisted_claim.session_id}/validate"
    headers = {"Idempotency-Key": "validate-conflict"}
    first = await test_client.post(
        endpoint, headers=headers,
        json={"manifest_id": persisted_claim.manifest_id, "claim_ids": [persisted_claim.claim_id], "mode": "safe_auto"},
    )
    second = await test_client.post(
        endpoint, headers=headers,
        json={"manifest_id": persisted_claim.manifest_id, "claim_ids": [persisted_claim.claim_id], "mode": "scientific"},
    )
    assert first.status_code == 202
    assert second.status_code == 409


async def test_cross_workspace_claim_history_is_hidden(test_client, workspace_a_claim, user_b_token) -> None:
    response = await test_client.get(
        f"/api/analysis/{workspace_a_claim.session_id}/claims/{workspace_a_claim.claim_id}/assessments",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert response.status_code == 404


async def test_workspace_viewer_cannot_start_validation(test_client, workspace_claim, viewer_token) -> None:
    response = await test_client.post(
        f"/api/analysis/{workspace_claim.session_id}/validate",
        headers={"Authorization": f"Bearer {viewer_token}", "Idempotency-Key": "viewer-validate"},
        json={"manifest_id": workspace_claim.manifest_id, "claim_ids": [workspace_claim.claim_id], "mode": "safe_auto"},
    )
    assert response.status_code == 403


async def test_session_credibility_is_claim_indexed_and_conservative(test_client, mixed_claims) -> None:
    response = await test_client.get(f"/api/analysis/{mixed_claims.session_id}/credibility")
    payload = response.json()["data"]
    assert set(payload["claims"]) == {"claim-calibrated", "claim-unverified"}
    assert payload["claims"]["claim-calibrated"]["credibility_tier"] == "calibrated_forecast"
    assert payload["claims"]["claim-unverified"]["credibility_tier"] == "scenario_exploration"
    assert payload["summary"]["credibility_tier"] == "scenario_exploration"
    assert payload["summary"]["confidence_score"] is None


async def test_simulation_completion_persists_base_claims_once(
    completion_coordinator, completed_session, frozen_manifest
) -> None:
    first = await completion_coordinator.finalize(
        completed_session.session_id, completed_session.job_id, frozen_manifest.manifest_id
    )
    second = await completion_coordinator.finalize(
        completed_session.session_id, completed_session.job_id, frozen_manifest.manifest_id
    )
    assert second == first
    assert [(claim.metric, claim.forecast_kind) for claim in first] == [("support", "probability")]
    assert await completion_coordinator.claim_count(completed_session.session_id) == 1
    assert (await completion_coordinator.latest_assessment(first[0].claim_id)).credibility_tier == "scenario_exploration"


async def test_simulation_finalization_rolls_back_claims_and_workflow_together(
    completion_coordinator, finalizing_session, frozen_manifest, workflow_repo,
    fail_before_workflow_event,
) -> None:
    with fail_before_workflow_event(), pytest.raises(InjectedCrash):
        await completion_coordinator.finalize(
            finalizing_session.session_id, finalizing_session.job_id, frozen_manifest.manifest_id
        )
    assert await completion_coordinator.claim_count(finalizing_session.session_id) == 0
    assert (await completion_coordinator.get_session(finalizing_session.session_id)).status == "finalizing"
    assert (await completion_coordinator.get_job(finalizing_session.job_id)).status == "finalizing"
    workflow = await workflow_repo.get_by_session_id(finalizing_session.session_id)
    assert (workflow.current_step, workflow.status) == ("simulation", "running")
    assert await workflow_repo.count_events(workflow.workflow_id, "simulation.completed") == 0

    claims = await completion_coordinator.finalize(
        finalizing_session.session_id, finalizing_session.job_id, frozen_manifest.manifest_id
    )
    workflow = await workflow_repo.get_by_session_id(finalizing_session.session_id)
    assert len(claims) == 1
    assert (workflow.current_step, workflow.status) == ("simulation", "awaiting_input")
    assert await workflow_repo.count_events(workflow.workflow_id, "simulation.completed") == 1


async def test_worker_recovers_stale_job_without_duplicate_replica(worker_factory, job_repo, execution_adapter) -> None:
    job = await job_repo.enqueue_validation_job(
        session_id="session-1", manifest_id="manifest-1", claim_ids=("claim-1",),
        mode="safe_auto", idempotency_key="recover-1",
    )
    await job_repo.mark_running(
        job.validation_job_id, owner_token="dead-worker",
        heartbeat_at=datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc),
    )
    execution_adapter.seed_existing_artifact(job.validation_job_id, "claim-1", seed=101)
    worker = worker_factory()
    await worker.recover_stale_jobs()
    await worker.process_once()
    assert execution_adapter.calls_for(job.validation_job_id, "claim-1", 101) == 0
    assert (await job_repo.get(job.validation_job_id)).status == "completed"


async def test_completion_is_atomic_when_any_assessment_insert_fails(
    job_repo, evidence_factory, assessment_factory
) -> None:
    job = await job_repo.enqueue_validation_job(
        session_id="session-1", manifest_id="manifest-1", claim_ids=("claim-1",),
        mode="safe_auto", idempotency_key="atomic-1",
    )
    await job_repo.mark_running(job.validation_job_id, owner_token="worker-1", heartbeat_at=utc_now())
    evidence = evidence_factory(validation_job_id=job.validation_job_id)
    duplicate = assessment_factory(assessment_id="duplicate", validation_job_id=job.validation_job_id)
    with pytest.raises(sqlite3.IntegrityError):
        await job_repo.complete_job_atomic(
            job.validation_job_id, owner_token="worker-1",
            evidence=(evidence,), assessments=(duplicate, duplicate),
        )
    assert await job_repo.list_evidence(job.validation_job_id) == ()
    assert await job_repo.list_assessments(job.validation_job_id) == ()
    assert (await job_repo.get(job.validation_job_id)).status == "running"


async def test_cancel_appends_terminal_claim_assessment(worker, job_repo, persisted_claim) -> None:
    job = await job_repo.enqueue_validation_job(
        session_id=persisted_claim.session_id, manifest_id=persisted_claim.manifest_id,
        claim_ids=(persisted_claim.claim_id,), mode="scientific", idempotency_key="cancel-validation-1",
    )
    await job_repo.request_cancel(job.validation_job_id)
    await worker.process_once()
    latest = await job_repo.latest_assessment(persisted_claim.claim_id)
    assert (await job_repo.get(job.validation_job_id)).status == "cancelled"
    assert latest.validation_status == "cancelled"
    assert latest.revision > 1
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_trend_analysis.py backend/tests/test_validation_worker.py backend/tests/test_simulation_worker.py backend/tests/api/test_analysis_api.py -q`

- [ ] **Step 3: Implement exact model contract**

```python
class TrendClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    claim_id: str
    session_id: str
    metric: str
    forecast_kind: Literal["probability", "continuous"]
    horizon: str
    direction: Literal["up", "down", "flat", "uncertain"]
    evidence_ids: tuple[str, ...]
    counter_signals: tuple[str, ...]
    method_version: str
    manifest_id: str
    created_at: datetime


class ClaimAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    assessment_id: str
    claim_id: str
    validation_job_id: str | None
    revision: int
    credibility_tier: CredibilityTier
    validation_status: Literal["not_applicable", "pending", "passed", "failed", "cancelled", "insufficient_evidence"]
    estimate: float | None
    interval: tuple[float, float] | None
    validation_evidence_id: str | None
    limitations: tuple[str, ...]
    created_at: datetime


class TrendClaimView(TrendClaim):
    assessment_revision: int
    credibility_tier: CredibilityTier
    validation_status: Literal["not_applicable", "pending", "passed", "failed", "cancelled", "insufficient_evidence"]
    estimate: float | None
    interval: tuple[float, float] | None
    validation_evidence_id: str | None
    limitations: tuple[str, ...]
```

Add `trend_claims` and append-only `claim_assessments` tables to `backend/database/schema.sql` and `backend/app/utils/migrations.py`. `trend_claims` is keyed by `claim_id` with indexed `session_id` and stores only immutable base claim facts, including explicit `forecast_kind`; evidence IDs and counter-signals use JSON text. Validation scope must exactly match the claim's stored `forecast_kind` and may never infer it from a metric name. `claim_assessments` is keyed by `assessment_id`, unique `(claim_id, revision)`, indexed by `claim_id` and `validation_job_id`, and stores the evolving estimate/tier/status/interval/limitations projection. Claim creation transactionally inserts assessment revision 1 as `scenario_exploration` + `insufficient_evidence` with null estimate/interval/evidence. A queued validation may append `pending`; successful evidence maps `model_estimate` or `calibrated_forecast` to `passed`, insufficient evidence maps to `insufficient_evidence`, and execution failure maps to `failed` with null estimate/interval. Non-null estimate/interval come only from the linked `ValidationEvidence`. Validation appends revision 2+ and never updates either the claim or an earlier assessment. API claim reads return a `TrendClaimView` composed from the base row plus highest assessment revision, while the exact assessments endpoint/repository method preserves every revision. Do not overload report JSON or global calibration tables.

`SimulationWorker` changes a successful engine run to `finalizing`, then calls `SimulationCompletionCoordinator` before exposing any completion. The coordinator reads only persisted artifacts, resolves the unique workflow by `session_id`, iterates the frozen manifest's explicit `MetricSpec` values, and uses deterministic `TrendAnalysisService` logic to build each claim. One shared SQLite `BEGIN IMMEDIATE` transaction inserts all base claims and revision-1 assessments, changes the simulation job/session to `completed`, advances the workflow revision to `simulation/awaiting_input`, and appends exactly one monotonic `simulation.completed` workflow event. No later callback is allowed to perform the workflow transition. Add unique `(session_id, manifest_id, metric, horizon, method_version)` and a unique completion-event correlation so retry returns the same claims and event. LLM narrative is not part of this hook. If claim, assessment, session/job, workflow revision, or event persistence fails, the entire transaction rolls back: artifacts remain, job/session stay `finalizing`, workflow stays `simulation/running`, and the worker retries/reconciles. Step 3 cannot expose the report CTA until this atomic finalization commits.

Add `validation_jobs` keyed by `validation_job_id`, unique `(session_id, idempotency_key)`, with statuses `queued|running|completed|failed|cancelled`; persist claim IDs, manifest ID, mode, canonical request hash, attempt count, owner token, heartbeat, cancel flag, next-attempt time, error code and timestamps. Canonicalize claim IDs by sorted unique order before hashing. Reusing a key with the identical manifest/claims/mode replays the same job; any hash mismatch returns HTTP 409 and discloses no prior job body. Before enqueueing, verify every claim belongs to the supplied frozen manifest and session; mismatch returns HTTP 409. `safe_auto` uses manifest thresholds without overrides. `scientific` runs the frozen manifest's configured replicas/backtest/sensitivity but cannot alter it.

`GET /credibility` returns `{claims: Record<claim_id, ClaimCredibility>, summary: SessionCredibility}`. Every claim entry is derived from that claim's latest assessment/evidence only. The optional summary uses the weakest tier across all current claims (`scenario_exploration < model_estimate < calibrated_forecast`), union of missing evidence and limitations, and always-null deprecated confidence fields; no UI/report may use the session summary as evidence for an individual claim. With zero claims the summary is `scenario_exploration` with `missing_evidence=("claims",)`.

`ValidationWorker` follows the existing `SimulationWorker` polling/lifespan pattern and is started/stopped in `backend/app/__init__.py`. It atomically claims one queued job, heartbeats every 15 seconds, checks cancellation between replicas/folds, and retries transient failures at 5s/30s/120s up to three attempts. Startup recovery requeues `running` jobs whose heartbeat is older than 120 seconds unless attempts are exhausted. `ValidationExecutionAdapter` calls existing `SwarmEnsemble`, `RetrospectiveValidator`, and `SensitivityAnalyzer`; absence of historical observations produces missing evidence, never a synthetic backtest. Every replica/backtest/sensitivity artifact carries `validation_job_id`, `claim_id`, manifest revision and deterministic seed/fold correlation, with DB unique constraints so retries reuse completed work.

After computation, build all `ValidationEvidence` and `ClaimAssessment` frozen values in memory. One `BEGIN IMMEDIATE` repository transaction rechecks job ownership/cancel state, allocates every evidence/assessment revision, inserts all claim-scoped evidence and assessments, and changes the job to `completed`; any failure rolls back the whole set. A retry first reconciles artifacts and existing job-linked rows, then either returns the already-completed result or resumes missing computation. Cancellation is also one terminal transaction: after worker acknowledgement it marks the job `cancelled` and appends a `validation_status="cancelled"` assessment for every requested claim. That revision copies the last non-pending tier/estimate/interval/evidence, adds a cancellation limitation, and prevents the latest view from remaining `pending`; completed immutable artifacts stay visible but do not promote the claim.

- [ ] **Step 4: Verify GREEN and commit**

Run: `.venv311/bin/python -m pytest backend/tests/test_trend_analysis.py backend/tests/test_validation_worker.py backend/tests/test_simulation_worker.py backend/tests/api/test_analysis_api.py -q`

Commit: `feat: add structured trend claims`

### Task 7: Remove caller and global confidence leakage

**Files:**
- Modify: `backend/app/api/simulation_macro.py`
- Modify: `backend/app/services/report_agent.py`
- Modify: `frontend/src/components/TrendReport.vue`
- Modify: `frontend/src/api/simulation.js`
- Test: `backend/tests/test_report.py`
- Create: `backend/tests/api/test_trend_narrative_api.py`

**Interfaces:**
- Consumes: saved `TrendClaim` IDs and claim-indexed credibility; the conservative session summary is display-only and never substitutes for claim evidence.
- Produces: narrative/report tools that cannot invent or import unrelated confidence; Task 15 binds those tools to immutable report-manifest assessment pins for export/share stability.

- [ ] **Step 1: Write failing tests**

```python
def test_trend_narrative_rejects_confidence_query(client):
    response = client.get("/api/simulation/s1/narrative?confidence_score=0.99")
    assert response.status_code == 422


async def test_report_validation_is_claim_scoped(monkeypatch):
    text = await _handle_get_validation_summary("s1", {"claim_id": "c1"}, object())
    assert "claim c1" in text
    assert "Historical prediction accuracy" not in text
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/api/test_trend_narrative_api.py backend/tests/test_report.py -q`

- [ ] **Step 3: Implement**

Remove `confidence_score`／`confidence_level` query parameters. Replace the missing `/confidence-score` frontend call with typed `/api/analysis/{session_id}/credibility`. `TrendReport.vue` must request only metrics returned by current claims; remove the fixed HK metric list from generic scenarios.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
.venv311/bin/python -m pytest backend/tests/api/test_trend_narrative_api.py backend/tests/test_report.py -q
cd frontend && npm run typecheck
```

Commit: `fix: scope trend confidence to verified claims`

---

## Phase B — Workflow truth and persistent shell

### Task 8: Make workflow persistence explicit and incremental

**Files:**
- Create: `backend/app/models/workflow.py`
- Create: `backend/app/services/workflow_repository.py`
- Create: `backend/app/services/workflow_action_service.py`
- Modify: `backend/database/schema.sql`
- Modify: `backend/app/utils/migrations.py`
- Modify: `backend/app/services/workflow_runner.py`
- Modify: `backend/app/api/workflow.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_workflow_repository.py`
- Create: `backend/tests/test_workflow_runner.py`
- Create: `backend/tests/test_workflow_restart.py`
- Create: `backend/tests/api/test_workflow_api.py`

**Interfaces:**
- Produces: monotonic `WorkflowEvent.id`, `WorkflowRun.revision`, incremental `after_event_id` API.
- Produces `POST /api/workflow/drafts` with `{"autopilot": false|true, "workspace_id": str|null}`; response is an owner/workspace-scoped persisted `graph/awaiting_input` workflow with no seed or job yet. Demo anonymous response additionally returns the one-time workflow capability.
- Produces server-gated actions: `submit_seed`, `start_simulation`, `generate_report`, `enter_interaction`, `rerun_with_manifest`, `cancel_current_job`, and `retry_current_step` through `POST /api/workflow/{workflow_id}/actions/{action}` with required `Idempotency-Key` header.
- `WorkflowActionService.execute(workflow_id: str, action: WorkflowAction, idempotency_key: str, payload: ActionPayload) -> WorkflowRun` is the only production transition entrypoint.
- Guided workflow uses `autopilot=false`. Express workflow may use `autopilot=true`, but it invokes the same action service and transition rules internally.
- Action payloads are exact discriminated request models: `submit_seed={seed_text, scenario_question, domain_pack_id, preset}`, where `preset` is nullable for Guided and one of the existing preset names for Express; `start_simulation={manifest_id}`, `generate_report={report_type:'full'|'summary'}`, `enter_interaction={}`, `rerun_with_manifest={manifest_id,label}`, `cancel_current_job={expected_job_kind, correlation_id}`, `retry_current_step={}`. `seed_text`, `scenario_question`, and rerun label pass existing prompt-security sanitizers before persistence or LLM use.

- [ ] **Step 1: Write failing repository/API tests**

```python
async def test_events_are_monotonic_and_incremental(repo):
    first = await repo.append_event("w1", "graph.started", "graph", {})
    second = await repo.append_event("w1", "graph.completed", "graph", {})
    assert second.id > first.id
    assert await repo.list_events("w1", after_event_id=first.id) == (second,)


async def test_server_step_is_monotonic(repo):
    await repo.advance("w1", step_index=3, status="running")
    with pytest.raises(InvalidWorkflowTransition):
        await repo.advance("w1", step_index=2, status="running")


async def test_start_simulation_requires_frozen_manifest(action_service, draft_manifest):
    with pytest.raises(InvalidWorkflowTransition, match="frozen manifest"):
        await action_service.execute("w1", "start_simulation", "key-1", {"manifest_id": draft_manifest.manifest_id})


async def test_create_guided_draft_starts_at_seed_input(test_client):
    response = await test_client.post("/api/workflow/drafts", json={"autopilot": False, "workspace_id": None})
    assert response.status_code == 201
    workflow = response.json()["data"]
    assert (workflow["current_step"], workflow["status"], workflow["autopilot"]) == (
        "graph", "awaiting_input", False,
    )


async def test_cross_workspace_user_cannot_cancel_workflow(test_client, workspace_a_workflow, user_b_token):
    response = await test_client.post(
        f"/api/workflow/{workspace_a_workflow.workflow_id}/actions/cancel_current_job",
        headers={"Authorization": f"Bearer {user_b_token}", "Idempotency-Key": "forbidden-cancel"},
        json={"expected_job_kind": "simulation", "correlation_id": workspace_a_workflow.last_receipt_id},
    )
    assert response.status_code == 404


async def test_completed_workflow_rerun_creates_child_without_mutating_parent(
    action_service, repo, runner, session_repo, manifest_repo,
    completed_report_workflow, frozen_manifest_revision,
):
    result = await action_service.execute(
        completed_report_workflow.workflow_id, "rerun_with_manifest", "rerun-1",
        {"manifest_id": frozen_manifest_revision.manifest_id, "label": "Higher regulation shock"},
    )
    parent = await repo.get_workflow(completed_report_workflow.workflow_id)
    child = await repo.get_workflow(result.spawned_workflow_id)
    assert parent == completed_report_workflow
    assert child.parent_workflow_id == parent.workflow_id
    assert child.parent_session_id == parent.session_id
    assert child.graph_id == parent.graph_id
    assert child.manifest_id == frozen_manifest_revision.manifest_id
    assert (child.current_step, child.status) == ("simulation", "queued")

    await runner.process_receipt(child.last_receipt_id)
    running_child = await repo.get_workflow(child.workflow_id)
    child_session = await session_repo.get(running_child.session_id)
    attested_manifest = await manifest_repo.get(child_session.manifest_id)
    assert running_child.session_id != parent.session_id
    assert child_session.manifest_id == frozen_manifest_revision.manifest_id
    assert child_session.manifest_hash == frozen_manifest_revision.manifest_hash
    assert attested_manifest.root_workflow_id == parent.root_workflow_id
    assert attested_manifest.authored_from_workflow_id == parent.workflow_id
    assert (await repo.get_workflow(parent.workflow_id)) == parent


@pytest.mark.parametrize(
    ("manifest_graph_id", "manifest_graph_revision"),
    [("graph-other", 3), ("graph-7", 4)],
)
async def test_rerun_rejects_graph_pin_mismatch_before_outbox_or_session(
    action_service, repo, session_repo, completed_report_workflow,
    frozen_manifest_revision_factory, manifest_graph_id, manifest_graph_revision,
):
    mismatched = frozen_manifest_revision_factory(
        graph_id=manifest_graph_id, graph_revision=manifest_graph_revision
    )
    before_sessions = await session_repo.count_for_root(completed_report_workflow.root_workflow_id)
    with pytest.raises(InvalidWorkflowTransition, match="graph pin"):
        await action_service.execute(
            completed_report_workflow.workflow_id, "rerun_with_manifest", "rerun-mismatch",
            {"manifest_id": mismatched.manifest_id, "label": "Invalid graph branch"},
        )
    assert await repo.count_outbox_for_workflow(completed_report_workflow.workflow_id) == 0
    assert await session_repo.count_for_root(completed_report_workflow.root_workflow_id) == before_sessions


async def test_legacy_quick_start_routes_through_autopilot_action(test_client, repo):
    response = await test_client.post(
        "/api/workflow/quick-start",
        headers={"Idempotency-Key": "express-1"},
        json={"seed_text": "A proposed transport policy", "scenario_question": "What changes?", "preset": "standard"},
    )
    assert response.status_code == 202
    workflow_id = response.json()["data"]["workflow_id"]
    workflow = await repo.get_workflow(workflow_id)
    assert workflow.autopilot is True
    assert await repo.count_outbox(workflow.last_receipt_id) == 1
    assert (await repo.get_receipt(workflow.last_receipt_id)).action == "submit_seed"


async def test_express_graph_completion_builds_manifest_then_enters_simulation(
    test_client, runner, repo, recommended_factory
):
    response = await test_client.post(
        "/api/workflow/quick-start",
        headers={"Idempotency-Key": "express-e2e-1"},
        json={"seed_text": "A proposed transport policy", "scenario_question": "What changes?", "preset": "standard"},
    )
    workflow_id = response.json()["data"]["workflow_id"]
    await runner.process_until_step(workflow_id, "simulation")
    workflow = await repo.get_workflow(workflow_id)
    manifest = await recommended_factory.get(workflow.manifest_id)
    assert manifest.status == "frozen"
    assert manifest.root_workflow_id == workflow_id
    assert manifest.authored_from_workflow_id == workflow_id
    assert workflow.current_step == "simulation"
    assert workflow.session_id is not None


async def test_express_recovers_crash_after_manifest_freeze_before_workflow_link(
    runner_factory, recommended_factory, repo, express_graph_completed_workflow
):
    crashing = runner_factory(crash_after_manifest_freeze=True)
    with pytest.raises(InjectedCrash):
        await crashing.process_once()
    frozen_before_restart = await recommended_factory.find_by_recommendation_key(
        express_graph_completed_workflow.recommendation_key
    )
    restarted = runner_factory(crash_after_manifest_freeze=False)
    await restarted.process_once()
    workflow = await repo.get_workflow(express_graph_completed_workflow.workflow_id)
    assert workflow.manifest_id == frozen_before_restart.manifest_id
    assert await recommended_factory.count_by_recommendation_key(
        express_graph_completed_workflow.recommendation_key
    ) == 1


async def test_duplicate_action_creates_one_outbox_item(action_service, repo, frozen_manifest):
    payload = {"manifest_id": frozen_manifest.manifest_id}
    first = await action_service.execute("w1", "start_simulation", "same-key", payload)
    second = await action_service.execute("w1", "start_simulation", "same-key", payload)
    assert second.session_id == first.session_id
    assert await repo.count_outbox(first.last_receipt_id) == 1


async def test_concurrent_duplicate_action_creates_one_outbox_item(action_service, repo, frozen_manifest):
    payload = {"manifest_id": frozen_manifest.manifest_id}
    first, second = await asyncio.gather(
        action_service.execute("w1", "start_simulation", "concurrent-key", payload),
        action_service.execute("w1", "start_simulation", "concurrent-key", payload),
    )
    assert first == second
    assert await repo.count_outbox(first.last_receipt_id) == 1


async def test_action_receipt_replays_after_service_restart(action_service, service_factory, repo, frozen_manifest):
    payload = {"manifest_id": frozen_manifest.manifest_id}
    first = await action_service.execute("w1", "start_simulation", "restart-key", payload)
    restarted = service_factory()
    second = await restarted.execute("w1", "start_simulation", "restart-key", payload)
    assert second == first
    assert await repo.count_outbox(first.last_receipt_id) == 1


async def test_crash_after_downstream_create_reconciles_without_duplicate(
    action_service, runner_factory, downstream_adapter, frozen_manifest
):
    workflow = await action_service.execute(
        "w1", "start_simulation", "crash-key", {"manifest_id": frozen_manifest.manifest_id}
    )
    crashing_runner = runner_factory(crash_after_adapter=True)
    with pytest.raises(InjectedCrash):
        await crashing_runner.process_once()
    restarted = runner_factory(crash_after_adapter=False)
    await restarted.recover_expired_outbox()
    await restarted.process_once()
    assert downstream_adapter.created_count(correlation_id=workflow.last_receipt_id) == 1
    assert (await restarted.repo.get_receipt(workflow.last_receipt_id)).status == "completed"


async def test_same_key_with_different_payload_conflicts(action_service, frozen_manifest):
    await action_service.execute(
        "w1", "start_simulation", "conflict-key", {"manifest_id": frozen_manifest.manifest_id}
    )
    with pytest.raises(IdempotencyConflict):
        await action_service.execute(
            "w1", "start_simulation", "conflict-key", {"manifest_id": "manifest-other"}
        )


async def test_cancel_queued_action_before_downstream_job_exists(action_service, repo, downstream_adapter):
    forward = await action_service.execute(
        "w1", "submit_seed", "build-queued",
        {"seed_text": "seed", "scenario_question": "question", "domain_pack_id": "public_narrative", "preset": None},
    )
    await action_service.execute(
        "w1", "cancel_current_job", "cancel-queued",
        {"expected_job_kind": "graph", "correlation_id": forward.last_receipt_id},
    )
    assert (await repo.get_outbox_by_receipt(forward.last_receipt_id)).status == "cancelled"
    assert downstream_adapter.created_count(correlation_id=forward.last_receipt_id) == 0
    assert (await repo.get_workflow("w1")).status == "cancelled"


async def test_lifespan_recovers_expired_outbox_and_stops_worker(
    app_factory, repo, downstream_adapter, expired_running_outbox
):
    app = app_factory()
    async with LifespanManager(app):
        await eventually(lambda: repo.get_receipt(expired_running_outbox.receipt_id), status="completed")
        assert downstream_adapter.created_count(correlation_id=expired_running_outbox.receipt_id) == 1
        assert app.state.workflow_runner.is_running is True
    assert app.state.workflow_runner.is_running is False


@pytest.mark.parametrize(
    ("step", "action", "allowed"),
    [
        ("graph", "submit_seed", True),
        ("graph", "start_simulation", False),
        ("environment", "start_simulation", True),
        ("simulation", "generate_report", True),
        ("report", "enter_interaction", True),
    ],
)
async def test_action_transition_matrix(action_service, test_db, step, action, allowed):
    await seed_workflow_row(test_db, workflow_id="w1", step=step, status="awaiting_input")
    if allowed:
        assert (await action_service.execute("w1", action, f"{step}-{action}", payload_for(action))).current_step is not None
    else:
        with pytest.raises(InvalidWorkflowTransition):
            await action_service.execute("w1", action, f"{step}-{action}", payload_for(action))
```

The test module defines `seed_workflow_row(test_db, workflow_id, step, status)` as a test-only SQL fixture helper and defines `payload_for` as `submit_seed -> {seed_text:'seed', scenario_question:'question', domain_pack_id:'public_narrative', preset:null}`, `start_simulation -> {manifest_id:'manifest-1'}`, `generate_report -> {report_type:'full'}`, `enter_interaction -> {}`, `rerun_with_manifest -> {manifest_id:'manifest-2',label:'Branch B'}`, `cancel_current_job -> {expected_job_kind:'simulation', correlation_id:'receipt-forward-1'}`, `retry_current_step -> {}`. The crash fixture wraps the adapter return boundary; no test-only method is added to production classes.

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_workflow_repository.py backend/tests/test_workflow_runner.py backend/tests/test_workflow_restart.py backend/tests/api/test_workflow_api.py -q`

- [ ] **Step 3: Implement repository and models**

Exact status values: `queued|running|awaiting_input|completed|degraded|failed|cancelled`. Exact step values: `graph|environment|simulation|report|interaction`. Add `owner_user_id`, `workspace_id`, guest capability hash, `root_workflow_id`, `parent_workflow_id`, `parent_session_id`, `branch_label`, `manifest_id`, `autopilot`, `revision`, `last_receipt_id` to workflow rows. A root workflow stores its own ID in `root_workflow_id`; every descendant copies it. The GET response includes `revision`, `events`, `last_event_id`; `?after_event_id=N` returns only later events but still returns current workflow summary. Every draft/read/action route uses `ResourceAuthorization`; outbox workers propagate stored ownership rather than a request principal.

Persist action ownership/results in `workflow_action_receipts`: `receipt_id`, `workflow_id`, `action`, `idempotency_key`, `request_hash`, `status` (`pending|completed|failed|cancelled`), `response_json`, `error_code`, `created_at`, and `updated_at`, with unique `(workflow_id, action, idempotency_key)` and an index on `workflow_id`. Persist a transactional outbox row with `outbox_id`, `receipt_id` unique, validated payload JSON, status (`pending|running|cancel_requested|completed|failed|cancelled`), owner token, lease expiry, attempts and timestamps. `WorkflowActionService.execute()` canonicalizes and hashes the validated payload, then in one `BEGIN IMMEDIATE` transaction checks the transition and inserts the pending receipt, pending outbox row, queued workflow revision and event. It performs no graph/simulation/report side effect inside the request.

`WorkflowRunner` claims outbox rows with a 120-second lease. Each downstream adapter receives `receipt_id` as its correlation key: graph/report job records and `simulation_jobs` add a unique correlation column. Creating or finding that durable downstream job is idempotent. After the adapter returns, one transaction stores artifact/job IDs, completes outbox/receipt and advances the workflow. If the process crashes after downstream creation but before that transaction, lease recovery invokes the adapter with the same correlation key, finds the existing downstream job, and reconciles instead of duplicating it. Terminal typed failures are persisted and replayed; transient failures retry at 5s/30s/120s. `enter_interaction` has no external side effect and completes in the original action transaction.

Make `WorkflowRunner` a lifespan-owned singleton with `start()`, `stop()`, `wake()`, `is_running`, a 1-second fallback poll and an internal `asyncio.Event` wakeup. In `backend/app/__init__.py`, after migrations and before `yield`, obtain it, call `recover_expired_outbox()` then `start()`, and store it on `app.state`; after `yield`, stop it before the DB write queue. Startup recovery returns expired `running` rows to pending and resumes expired `cancel_requested` rows through cancellation reconciliation; pending rows need no mutation. Graceful stop prevents new claims, awaits/cancels the loop, and releases this owner's unfinished leases to pending/cancel-requested. Every successful action commit calls `wake()` best-effort, but durability depends on polling, not in-memory wakeup. Failure to start the runner is a startup error outside demo mode, not a warning-only degraded success.

`POST /api/workflow/drafts` is the only blank-workflow initializer. `/process/quick` calls it once when no `workflowId` is present, then replaces the route query with the returned ID before showing Step 1. Existing `/api/workflow/quick-start` and `/quick-start/upload` become compatibility wrappers: create `autopilot=true` draft, invoke the same `submit_seed` action with the request idempotency key and requested/default preset, wake `WorkflowRunner`, and return the workflow ID; they must delete the direct `asyncio.create_task(runner.run(...))` path. On Express graph completion, the runner calls `RecommendedManifestFactory.create_and_freeze()` using the persisted domain/preset, stores the manifest ID, then invokes `start_simulation` through `WorkflowActionService`. All later Express transitions also use that action service, never direct step/status edits.

Transition contract:

- `submit_seed`: allowed only at `graph/awaiting_input`; starts graph build. Completion stores `graph_id`, advances to `environment/awaiting_input`.
- `start_simulation`: allowed at a normal root `environment/awaiting_input`, or for a newly created rerun child at `simulation/queued`. It requires a frozen manifest whose `root_workflow_id` equals the target workflow's `root_workflow_id`, whose graph ID/revision equals that workflow's retained graph, and whose `parent_manifest_id` lineage is traceable to the parent session's attested manifest for a rerun child. `ResourceAuthorization`, `WorkflowActionService`, the outbox adapter, and `SimulationConfigAdapter` all enforce the same root/graph/lineage rule. It creates one new session/job, stores `session_id`, attests `manifest_id` plus `manifest_hash`, and advances to `simulation/running`.
- Only `SimulationCompletionCoordinator` may emit simulation completion: base claims, initial assessments, simulation job/session completion, workflow revision/state, and the monotonic completion event commit in the same `BEGIN IMMEDIATE` transaction defined in Task 6. There is no post-commit transition gap. It does not auto-generate a report when `autopilot=false`.
- `generate_report`: allowed only at `simulation/awaiting_input`; starts report generation and advances to `report/running`. Completion stores `report_id` and changes to `report/awaiting_input`.
- `enter_interaction`: allowed only at `report/awaiting_input`; advances to `interaction/completed` without creating another session/report.
- `rerun_with_manifest`: allowed on a workflow whose simulation has completed and is currently `simulation/awaiting_input`, `report/awaiting_input`, or `interaction/completed`. It requires a different frozen manifest revision with the same `root_workflow_id` and graph, `authored_from_workflow_id` equal to the invoking branch, and `parent_manifest_id` lineage traceable to that branch's attested session manifest. It creates a child workflow in one transaction, copying owner/workspace/root/graph but not session/report IDs, recording parent workflow/session and label, then queues the child's `start_simulation` through the same action/outbox machinery. Parent state and artifacts never change. The action response includes `spawned_workflow_id`; retries return the same child through the receipt.
- `cancel_current_job`: allowed only while graph/simulation/report is `queued|running`; `correlation_id` must equal the current forward action receipt, so it exists before any downstream job ID. If its outbox is still pending, one transaction marks the forward outbox/receipt cancelled, the cancellation action receipt completed, and the workflow cancelled without dispatch. If already claimed/created, mark the forward outbox `cancel_requested`; the runner resolves any downstream job through the correlation key, invokes the matching cancel adapter, and only acknowledged cancellation marks the forward receipt/workflow cancelled and the cancellation receipt completed. It is cancellation, not pause, and never calls `/resume`.
- `retry_current_step`: allowed only from `failed|cancelled|degraded`; it copies the last forward action's validated payload into a new outbox row linked by `parent_receipt_id`, uses the new request idempotency key/correlation ID, retains prior artifacts for audit, and returns the same step as `queued`.
- `autopilot=true` calls the next allowed action through the same service after each completion event; it never mutates step fields directly.
- Reusing an `Idempotency-Key` with the same canonical request returns the persisted receipt result, including after restart; reusing it with a different request returns HTTP 409. A different key on an already-running/completed action also returns HTTP 409 and starts no duplicate job.

- [ ] **Step 4: Verify GREEN and commit**

Run: `.venv311/bin/python -m pytest backend/tests/test_workflow_repository.py backend/tests/test_workflow_runner.py backend/tests/test_workflow_restart.py backend/tests/api/test_workflow_api.py -q`

Commit: `feat: persist incremental workflow events`

### Task 9: Add frontend workflow, graph and mode composables

**Files:**
- Modify: `frontend/src/api/workflow.js`
- Modify: `frontend/src/api/graph.js`
- Create: `frontend/src/api/validation.ts`
- Create: `frontend/src/api/analysis.ts`
- Create: `frontend/src/types/workbench.ts`
- Create: `frontend/src/composables/useWorkflowRun.js`
- Create: `frontend/src/composables/usePersistentGraph.js`
- Create: `frontend/src/composables/useWorkbenchMode.js`
- Create: `frontend/tests/e2e/helpers/workbenchMocks.js`
- Create: `frontend/tests/e2e/workflow-resume.spec.js`

**Interfaces:**
- `useWorkflowRun(workflowId: string | null)` produces readonly `workflow`, `events`, `error`, plus `ensureDraft(autopilot)`, `executeAction`, `refresh`, `stop`.
- `usePersistentGraph()` produces graph data/state and guards stale async IDs.
- `useWorkbenchMode()` produces `mode: 'guided'|'expert'`, persisted under `murmura_workbench_mode`.
- Every Step emits one `graph-command` event whose payload is the `GraphCommand` union below; `Process.vue` is the only listener and delegates it to `usePersistentGraph.applyCommand()`.

```ts
export type GraphNode = Readonly<Record<string, unknown> & { id: string }>
export type GraphEdge = Readonly<Record<string, unknown> & { id: string; source_id: string; target_id: string }>

export type GraphOverlay = Readonly<{
  kind: 'build' | 'population' | 'simulation' | 'evidence' | 'interaction'
  round: number | null
  highlightedNodeIds: readonly string[]
  highlightedEdgeIds: readonly string[]
  communityIds: Readonly<Record<string, string>>
  contagionAgentIds: readonly string[]
  evidenceIds: readonly string[]
  revision: number
}>

export type GraphWorkspaceState = Readonly<{
  graphId: string | null
  nodes: readonly GraphNode[]
  edges: readonly GraphEdge[]
  selectedNodeId: string | null
  selectedEdgeId: string | null
  focusedNodeId: string | null
  round: number | null
  overlay: GraphOverlay | null
  loading: boolean
  error: string | null
  revision: number
}>

export type GraphCommand =
  | Readonly<{ type: 'replace'; graphId: string; nodes: readonly GraphNode[]; edges: readonly GraphEdge[]; revision: number }>
  | Readonly<{ type: 'snapshot'; graphId: string; round: number; nodes: readonly GraphNode[]; edges: readonly GraphEdge[]; revision: number }>
  | Readonly<{ type: 'overlay'; overlay: GraphOverlay }>
  | Readonly<{ type: 'focus'; nodeId: string | null; edgeId: string | null }>
  | Readonly<{ type: 'failure'; graphId: string | null; message: string; revision: number }>
```

- [ ] **Step 1: Write failing resume and mode tests plus shared mock helper**

`workbenchMocks.js` exports `installWorkbenchMocks(page, options)`; options include `stepIndex`, `status`, `graphId`, `sessionId`, `reportId`, `credibility`, `claims`, `validationJobStatus`, `receiptId`, and `failRoute`. It returns inspection helpers including `draftCreateCount()` and `lastValidationRequest()`. Its default graph fixture contains nodes `node-1`, `node-7` and edge `edge-1`.

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('restores the server step and saved expert mode', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 3, status: 'running' })
  await page.addInitScript(() => localStorage.setItem('murmura_workbench_mode', 'expert'))
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('workflow-step')).toHaveText('03')
  await expect(page.getByRole('button', { name: /Expert|專家/ })).toHaveAttribute('aria-pressed', 'true')
})

test('creates one guided draft when route has no workflow id', async ({ page }) => {
  const mocks = await installWorkbenchMocks(page, { stepIndex: 1, status: 'awaiting_input' })
  await page.goto('/process/quick')
  await expect.poll(() => new URL(page.url()).searchParams.get('workflowId')).toBe('w-created')
  expect(mocks.draftCreateCount()).toBe(1)
  await expect(page.getByLabel(/Reality seed|現實種子/)).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/workflow-resume.spec.js`

- [ ] **Step 3: Implement composables**

When the route has no workflow ID, `ensureDraft(false)` calls `POST /api/workflow/drafts` exactly once with the selected workspace, updates internal state, and `Process.vue` uses `router.replace` to persist `workflowId` before mounting Step 1. In demo anonymous mode, store the one-time capability only under `sessionStorage('murmura_workflow_capability:<workflowId>')` and attach it as `X-Workflow-Token`; never place it in URL, logs or localStorage. `useWorkflowRun` then starts one 1500ms poll, passes `after_event_id`, captures workflow ID before await, ignores stale responses, and clears timer on `stop()`/unmount. `executeAction` generates a UUID idempotency key per deliberate user action and reuses it only for network retry of the same canonical payload. `usePersistentGraph` retains last-good graph on request failure. Expose readonly state; mutations stay internal.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
cd frontend
npm run typecheck
npx playwright test tests/e2e/workflow-resume.spec.js
```

Commit: `feat: add resilient workbench composables`

### Task 10: Build the persistent graph workbench shell

**Files:**
- Create: `frontend/src/components/workbench/WorkbenchShell.vue`
- Create: `frontend/src/components/workbench/WorkbenchHeader.vue`
- Create: `frontend/src/components/workbench/WorkflowRail.vue`
- Create: `frontend/src/components/workbench/PersistentGraphPane.vue`
- Create: `frontend/src/components/workbench/GraphEvidencePanel.vue`
- Modify: `frontend/src/views/Process.vue`
- Modify: `frontend/src/components/GraphPanel.vue`
- Modify: `frontend/src/i18n/zh-TW.js`
- Modify: `frontend/src/i18n/en-US.js`
- Create: `frontend/tests/e2e/persistent-graph.spec.js`

**Interfaces:**
- `PersistentGraphPane` is the only owner of `GraphPanel`.
- Step components emit graph overlays/data; they never mount `GraphPanel`.

- [ ] **Step 1: Write failing identity/state test**

```js
test('keeps one graph instance across all five steps', async ({ page }) => {
  await page.goto('/process/quick')
  const graph = page.getByTestId('persistent-rag-graph')
  await expect(graph).toHaveCount(1)
  const instanceId = await graph.getAttribute('data-instance-id')
  for (const step of ['ENV', 'SIM', 'REPORT', 'INTERACT']) {
    await page.getByRole('button', { name: step }).click()
    await expect(graph).toHaveCount(1)
    await expect(graph).toHaveAttribute('data-instance-id', instanceId)
  }
})
```

The test routes API responses so each step is unlocked; do not add production-only test bypasses.

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/persistent-graph.spec.js`

- [ ] **Step 3: Implement shell**

Desktop uses CSS Grid with graph/task-panel columns. Mobile uses task panel plus a persistent Graph button/bottom sheet; the graph component remains mounted and is hidden with layout/CSS, not `v-if`. Move process rail/header/layout out of `Process.vue`. Remove hardcoded labels from `GraphPanel.vue` and translate them.

Delete `Process.vue` local `nextStep()` and all completion handlers that increment `currentStep`. `currentStep` is computed only from server `workflow.current_step`; rail clicks may inspect an already completed step but cannot mutate workflow state. Each primary CTA calls the Task 8 action endpoint, waits for the returned workflow revision, then lets server state change the visible step.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
cd frontend
npm run typecheck
npm run build
npx playwright test tests/e2e/persistent-graph.spec.js tests/e2e/process-smoke.spec.js
```

Commit: `feat: add persistent RAG workbench shell`

---

## Phase C — Guided steps and Expert controls

### Task 11: Integrate Step 1 graph build

**Files:**
- Create: `frontend/src/components/workbench/steps/SeedInputPanel.vue`
- Create: `frontend/src/components/workbench/steps/GraphBuildProgress.vue`
- Modify: `frontend/src/components/Step1GraphBuild.vue`
- Create: `frontend/tests/e2e/guided-graph-build.spec.js`

**Interfaces:**
- Step 1 emits only `graph-command` with the shared `GraphCommand` union. Build progress is read from typed workflow events; successful graph refresh emits `replace`, and request failure emits `failure` without discarding the last-good graph.

- [ ] **Step 1: Write failing guided-flow test**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('builds the world with one guided action', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 1 })
  await page.goto('/process/quick')
  await expect(page.getByLabel(/Reality seed|現實種子/)).toHaveCount(1)
  await expect(page.getByTestId('primary-step-action')).toHaveCount(1)
  await expect(page.getByText(/Extractor model|抽取模型/)).toHaveCount(0)
  await page.getByLabel(/Reality seed|現實種子/).fill('A proposed transport policy')
  await page.getByTestId('primary-step-action').click()
  await expect(page.getByTestId('graph-node-count')).not.toHaveText('0')
  await page.getByTestId('graph-node-node-7').click()
  await expect(page.getByTestId('graph-evidence-panel')).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/guided-graph-build.spec.js`

- [ ] **Step 3: Implement and split**

Remove Step 1's internal `GraphPanel`. Preserve upload/analyze helpers, but the primary Build CTA calls workflow action `submit_seed` instead of calling graph build and local `nextStep()` directly. Delete `getGraphStatus()` and its nonexistent `/graph/{id}/status` call. Build progress comes from typed workflow events; graph content refreshes through `GET /api/graph/{graph_id}` after graph event revisions. Captured graph/workflow IDs must be checked after every await. Emit only the shared `GraphCommand` union. Keep Step wrapper below 800 lines by extracting input/progress panels.

While graph build is queued/running, replace the forward CTA with a secondary `Cancel build` control that calls `cancel_current_job` using the workflow's current forward-action receipt ID, which is available before a graph job exists. Acknowledged cancellation shows the retained seed/artifacts and one `Retry` action wired to `retry_current_step`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd frontend && npm run typecheck && npx playwright test tests/e2e/guided-graph-build.spec.js tests/e2e/persistent-graph.spec.js`

Commit: `feat: connect graph build to persistent pane`

### Task 12: Integrate Step 2 Guided and Scientific Lab manifest

**Files:**
- Create: `frontend/src/components/workbench/ScientificLabDrawer.vue`
- Create: `frontend/src/components/workbench/steps/PopulationSummary.vue`
- Create: `frontend/src/components/workbench/steps/ExperimentManifestPreview.vue`
- Modify: `frontend/src/components/Step2EnvSetup.vue`
- Reuse without modification: `backend/app/models/request.py`, `backend/app/models/simulation_config.py`, existing simulation create/start API
- Create: `frontend/tests/e2e/scientific-lab.spec.js`

**Interfaces:**
- Guided creates same immutable manifest as Expert.
- Expert edits make manifest dirty; completed results are never silently rewritten.

- [ ] **Step 1: Write failing tests**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('keeps scientific controls behind the expert drawer', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 2 })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('population-summary')).toBeVisible()
  await expect(page.getByTestId('primary-step-action')).toHaveCount(1)
  await page.getByRole('button', { name: /Expert|專家/ }).click()
  for (const tab of [/World & population|世界與人口/, /Experiment|實驗/, /Models & cost|模型與成本/, /Validation & provenance|驗證與來源/]) {
    await expect(page.getByRole('tab', { name: tab })).toBeVisible()
  }
  await page.getByLabel(/Rounds|回合/).fill('24')
  await expect(page.getByTestId('manifest-dirty')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button', { name: /Expert|專家/ })).toHaveAttribute('aria-pressed', 'true')
})

test('reruns a completed result as an immutable child branch', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 4, completed: true })
  await page.goto('/process/quick?workflowId=w-completed')
  await page.getByRole('button', { name: /Expert|專家/ }).click()
  await page.getByRole('button', { name: /New revision|新增修訂/ }).click()
  await page.getByLabel(/Rounds|回合/).fill('24')
  await page.getByRole('button', { name: /Freeze revision|凍結修訂/ }).click()
  await page.getByRole('button', { name: /Run as new branch|作為新分支執行/ }).click()
  await expect(page).toHaveURL(/workflowId=w-child/)
  await expect(page.getByTestId('branch-parent')).toContainText('w-completed')
  await expect(page.getByTestId('workflow-step')).toHaveText(/Simulation|模擬/)
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/scientific-lab.spec.js`

- [ ] **Step 3: Implement**

Reuse existing Step 2 beginner/advanced data and preflight; do not duplicate config models. Guided inference calls `POST /api/manifests/recommended`, which uses `RecommendedManifestFactory.create_draft()` so Guided and Express share identical zero-config logic. Every control that can change results—agent/distribution, platforms, shocks, rounds/preset, full resolved hooks, model routing, dataset pins and cost cap—edits the typed `SimulationConfigSnapshot` inside that draft. Expert edits use `PATCH` while draft. The Start CTA freezes that exact revision, then calls workflow action `start_simulation` with one idempotency key; the backend constructs the existing create request only through `SimulationConfigAdapter.from_manifest()`. Edits after freeze call `/revisions`, create a new draft with `parent_manifest_id`, and show re-run required; they never mutate the running/completed session manifest. From a completed result, freezing that revision exposes `Run as new branch`, which invokes `rerun_with_manifest`, switches to the returned child workflow, and renders parent lineage while leaving the parent session/report unchanged. Move advanced sections into drawer slots. Emit a `population` `GraphOverlay` for KG node → agent/platform identity mapping.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd frontend && npm run typecheck && npx playwright test tests/e2e/scientific-lab.spec.js`

Commit: `feat: add guided and scientific experiment setup`

### Task 13: Integrate Step 3 live simulation

**Files:**
- Create: `frontend/src/components/workbench/steps/SimulationControls.vue`
- Create: `frontend/src/components/workbench/steps/SimulationEventFeed.vue`
- Modify: `frontend/src/components/Step3Simulation.vue`
- Create: `frontend/tests/e2e/live-simulation.spec.js`

**Interfaces:**
- Step 3 emits snapshots, selected round, community/faction/event overlays; persistent graph owns rendering.

- [ ] **Step 1: Write failing test**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('updates the persistent graph from live simulation events', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 3, status: 'running' })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('persistent-rag-graph')).toHaveCount(1)
  await expect(page.getByTestId('simulation-round')).toHaveText('7 / 20')
  await expect(page.getByTestId('simulation-event-feed')).toContainText('policy response')
  await expect(page.locator('[data-component="GraphPanel"]')).toHaveCount(1)
})

test('offers one report action only after simulation completion', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 3, status: 'awaiting_input', currentRound: 20 })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('primary-step-action')).toHaveText(/Generate report|生成報告/)
  await page.getByTestId('primary-step-action').click()
  await expect(page.getByTestId('workflow-step')).toHaveText('04')
})

test('cancels a running simulation without exposing general pause', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 3, status: 'running', receiptId: 'receipt-sim-1' })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByRole('button', { name: /Pause|暫停/ })).toHaveCount(0)
  await page.getByRole('button', { name: /Cancel simulation|取消模擬/ }).click()
  await expect(page.getByTestId('workflow-status')).toContainText(/Cancelled|已取消/)
  await expect(page.getByRole('button', { name: /Retry|重試/ })).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/live-simulation.spec.js`

- [ ] **Step 3: Implement**

Move Step 3 graph props/events to the persistent pane through `snapshot` and `simulation` overlay `GraphCommand` values. Preserve unmount guard at top of `ws.onclose`; clear every timeout/interval; keep last-good snapshot when a temporal request fails. Do not add a general Pause API: existing `/resume` remains cost-cap recovery only. While queued/running, the secondary cancel control invokes `cancel_current_job` with the current forward-action receipt correlation ID; cancelled/failed state offers one `retry_current_step` action. After simulation completion, the sole primary CTA invokes workflow action `generate_report`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd frontend && npm run typecheck && npx playwright test tests/e2e/live-simulation.spec.js tests/e2e/persistent-graph.spec.js`

Commit: `feat: connect live simulation to persistent graph`

---

## Phase D — Evidence-backed results

### Task 14: Add shared scientific evidence strip

**Files:**
- Create: `frontend/src/components/workbench/ScientificEvidenceStrip.vue`
- Create: `frontend/src/components/workbench/ClaimCredibilityBadge.vue`
- Create: `frontend/src/components/workbench/TrendClaimList.vue`
- Create: `frontend/src/components/workbench/ValidationControls.vue`
- Modify: `frontend/src/components/ConfidenceBadge.vue`
- Create: `frontend/tests/e2e/credibility.spec.js`

**Interfaces:**
- Consumes typed `TrendClaimView[]` and `ConfidenceResult`.
- Produces consistent tier, missing evidence, trend horizon/direction/range/stability display.
- `ValidationControls` submits all selected claim IDs with the current frozen manifest to `POST /api/analysis/{session_id}/validate`, polls the returned job endpoint, and cancels through the validation-job cancel endpoint.

- [ ] **Step 1: Write failing credibility tests**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

for (const fixture of [
  { tier: 'scenario_exploration', text: /未驗證|Unverified/, percentage: false },
  { tier: 'model_estimate', text: /模型估算|Model estimate/, percentage: false },
  { tier: 'calibrated_forecast', text: /已校準預測|Calibrated forecast/, percentage: false },
]) {
  test(`renders ${fixture.tier} without inventing certainty`, async ({ page }) => {
    await installWorkbenchMocks(page, { stepIndex: 4, credibility: fixture.tier })
    await page.goto('/process/quick?express=1&workflowId=w1')
    const badge = page.getByTestId('claim-credibility')
    await expect(badge).toHaveText(fixture.text)
    await expect(badge.locator('[data-value="percentage"]')).toHaveCount(fixture.percentage ? 1 : 0)
    await expect(badge).toHaveAttribute('aria-label', /.+/)
  })
}

test('starts and monitors claim-scoped validation without blocking report flow', async ({ page }) => {
  const mocks = await installWorkbenchMocks(page, {
    stepIndex: 3, status: 'awaiting_input', credibility: 'scenario_exploration', validationJobStatus: 'queued',
  })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await page.getByRole('button', { name: /Improve evidence|改善證據/ }).click()
  expect(mocks.lastValidationRequest()).toEqual({
    manifest_id: 'manifest-1', claim_ids: ['claim-1'], mode: 'safe_auto',
  })
  await expect(page.getByTestId('validation-job-status')).toContainText(/Queued|排隊中/)
  await page.getByRole('button', { name: /Cancel validation|取消驗證/ }).click()
  await expect(page.getByTestId('validation-job-status')).toContainText(/Cancelled|已取消/)
  await expect(page.getByRole('button', { name: /Generate report|生成報告/ })).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/credibility.spec.js`

- [ ] **Step 3: Implement**

Never render a composite confidence percentage or high/medium/low label. For `model_estimate`, show replica completion, MCSE, interval and stability. For `calibrated_forecast`, additionally show proper loss versus naive baseline, fold count and interval coverage where applicable. `scenario_exploration` shows missing evidence and limitations. Deprecated `confidence_score`/`confidence_level` values are ignored by this component.

Step 3 completion and Step 4 load claims immediately after the simulation-completion event; an empty claim list is an actionable error, not a valid completed state. Guided shows a non-blocking secondary `Improve evidence` action using `safe_auto`; report generation remains the single primary forward CTA at Step 3. Expert exposes `safe_auto|scientific`, manifest-derived replica/backtest/sensitivity summary and estimated cost before submit. Capture `session_id`, `manifest_id` and selected claim IDs before every request; poll the exact validation job every 1500ms, stop on terminal state/unmount, refresh claim-indexed credibility after completion, and call the dedicated validation cancel endpoint on cancel. A cancelled job renders the terminal cancelled assessment and can be restarted only with a new idempotency key.

Do not map `null` to 0 or medium. Existing `ConfidenceBadge` may remain for legacy consumers, but the new claim badge uses tiers and explicit missing evidence. Add accessible textual limitations.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd frontend && npm run typecheck && npx playwright test tests/e2e/credibility.spec.js`

Commit: `feat: show fail-closed scientific evidence`

### Task 15: Integrate Step 4 report timeline and graph evidence

**Files:**
- Create: `backend/app/models/report_manifest.py`
- Create: `backend/app/services/report_snapshot_service.py`
- Modify: `backend/app/api/report.py`
- Modify: `backend/app/services/report_agent.py`
- Modify: `backend/database/schema.sql`
- Modify: `backend/app/utils/migrations.py`
- Create: `backend/tests/test_report_snapshot.py`
- Create: `frontend/src/components/workbench/steps/ReportProgress.vue`
- Create: `frontend/src/components/workbench/steps/ReportDocumentPane.vue`
- Modify: `frontend/src/components/Step4Report.vue`
- Modify: `frontend/src/components/workbench/GraphEvidencePanel.vue`
- Create: `frontend/tests/e2e/report-evidence.spec.js`

**Interfaces:**
- Produces immutable `ReportManifest(report_manifest_id, report_id, report_revision, session_id, manifest_id, claim_pins, created_at)` where each pin is `(claim_id, assessment_revision, validation_evidence_id)`.
- Narrative, saved HTML/Markdown, PDF and share responses resolve claims only through that report manifest.
- Report tools expose names, public input summaries, status, evidence counts and results; never private reasoning.
- Evidence tags emit controlled node/edge IDs to persistent graph focus API.

- [ ] **Step 1: Write failing report/evidence test**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('links report evidence back to the graph safely', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 4, reportMarkdown: '[bad](javascript:alert(1)) [[N:node-7]]' })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('report-progress')).toBeVisible()
  await expect(page.getByTestId('report-tool-status')).toContainText(/complete|完成/)
  await page.locator('[data-evidence-id="node-7"]').click()
  await expect(page.getByTestId('persistent-rag-graph')).toHaveAttribute('data-focused-node', 'node-7')
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0)
})
```

Add backend snapshot test:

```python
async def test_report_exports_keep_pinned_assessments_after_later_validation(
    report_snapshot_service, claim_repo, report_exporter, persisted_claim
) -> None:
    first = await report_snapshot_service.create_for_session(
        report_id="report-1", session_id=persisted_claim.session_id, manifest_id=persisted_claim.manifest_id
    )
    assert first.claim_pins[0].assessment_revision == 1
    await claim_repo.append_validation_assessment(
        persisted_claim.claim_id, "validation-job-2", calibrated_result(), calibrated_evidence()
    )
    html = await report_exporter.render_html("report-1")
    pdf_source = await report_exporter.render_pdf_source("report-1")
    shared = await report_exporter.share_payload("report-1")
    assert all(item.credibility_tier == "scenario_exploration" for item in (html, pdf_source, shared))
    second = await report_snapshot_service.create_for_session(
        report_id="report-2", session_id=persisted_claim.session_id, manifest_id=persisted_claim.manifest_id
    )
    assert second.report_revision == first.report_revision + 1
    assert second.claim_pins[0].assessment_revision == 2
```

- [ ] **Step 2: Verify RED**

Run: `.venv311/bin/python -m pytest backend/tests/test_report_snapshot.py -q && cd frontend && npx playwright test tests/e2e/report-evidence.spec.js`

- [ ] **Step 3: Implement with audited upstream reuse**

Before copying any MiroFish Step4 excerpts, update reuse ledger to `modified`, add source header, and update combined licence metadata/notices as defined in Task 1. Reuse only collapsible-section/timeline interaction that is smaller than writing/adapting Murmura equivalents; bind it to Murmura claim/evidence APIs and `safeMarkdown`.

At `generate_report` action acceptance, `ReportSnapshotService` uses one transaction to allocate the next session report revision, read each current claim's exact latest assessment, insert ordered `report_claim_pins`, and attach `report_manifest_id` to the durable report job/correlation receipt. Pins are immutable and require the same session/frozen manifest. `ReportAgent`, stored report content, HTML/PDF exporters and share endpoint receive only the pinned `TrendClaimView` projection; they never call latest-claim lookup. Validation finishing later does not alter an existing report. A user who wants newer evidence generates a new `report_id`/report revision; no in-place refresh is permitted.

Report manifests inherit `owner_user_id`, `workspace_id` and root workflow ID. Generation/export/PDF/share-token creation requires write authorization; normal report reads require read authorization. A valid existing share token bypasses workspace membership for that pinned report only and grants no claim-history, workflow or validation access. Add cross-workspace 404 and viewer-share-creation 403 cases to `backend/tests/test_report_snapshot.py`.

While report status is `running`, show progress and no forward CTA. When workflow reaches `report/awaiting_input`, show exactly one primary `Explore result` CTA; it invokes workflow action `enter_interaction` and waits for the returned server revision before Step 5 becomes active.

During report generation, expose a secondary `Cancel report` control wired to `cancel_current_job` with the current forward-action receipt correlation ID; cancelled/failed report state exposes `retry_current_step`. Add these assertions to `report-evidence.spec.js` using mocked queued/running/cancelled workflow states.

- [ ] **Step 4: Verify GREEN and commit**

Run: `.venv311/bin/python -m pytest backend/tests/test_report_snapshot.py backend/tests/test_report.py -q && cd frontend && npm run typecheck && npm run build && npx playwright test tests/e2e/report-evidence.spec.js`

Commit: `feat: link report evidence to the world graph`

### Task 16: Integrate Step 5 interaction and branch exploration

**Files:**
- Create: `frontend/src/components/workbench/steps/InteractionTargetPicker.vue`
- Create: `frontend/src/components/workbench/steps/BranchComparisonPanel.vue`
- Modify: `frontend/src/components/Step5Interaction.vue`
- Create: `frontend/tests/e2e/interaction-graph.spec.js`

**Interfaces:**
- Per-target chat histories remain separate; answer citations focus graph entities; branch differences update overlay without replacing base graph.

- [ ] **Step 1: Write failing interaction test**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('keeps target histories and graph citations isolated', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 5 })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await page.getByRole('button', { name: /Report Agent/ }).click()
  await page.getByLabel(/Message|訊息/).fill('Report question')
  await page.getByRole('button', { name: /Send|傳送/ }).click()
  await page.getByRole('button', { name: /Agent A/ }).click()
  await page.getByLabel(/Message|訊息/).fill('Agent question')
  await page.getByRole('button', { name: /Send|傳送/ }).click()
  await page.getByRole('button', { name: /Report Agent/ }).click()
  await expect(page.getByTestId('chat-history')).toContainText('Report question')
  await expect(page.getByTestId('chat-history')).not.toContainText('Agent question')
  await page.locator('[data-evidence-id="node-7"]').click()
  await expect(page.getByTestId('persistent-rag-graph')).toHaveAttribute('data-focused-node', 'node-7')
  await page.getByRole('button', { name: /What-If/ }).click()
  await expect(page.getByTestId('branch-comparison')).toContainText(/Base|基準/)
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/interaction-graph.spec.js`

- [ ] **Step 3: Implement with audited upstream reuse**

Extract target/history interaction; do not duplicate the report document pane. If MiroFish Step5 excerpts are copied, follow Task 1 notice/metadata gate. Keep agent/report APIs and memory context from Murmura.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd frontend && npm run typecheck && npx playwright test tests/e2e/interaction-graph.spec.js`

Commit: `feat: connect deep interaction to graph evidence`

---

## Phase E — Accessibility, resilience and whole-system verification

### Task 17: Complete mobile, keyboard, i18n and failure states

**Files:**
- Modify: all new workbench components from Tasks 9–15
- Modify: `frontend/src/i18n/zh-TW.js`
- Modify: `frontend/src/i18n/en-US.js`
- Create: `frontend/tests/e2e/workbench-accessibility.spec.js`
- Create: `frontend/tests/e2e/workbench-failures.spec.js`

**Interfaces:**
- Produces: equivalent textual graph navigation, mobile graph access, reduced-motion and actionable failures.

- [ ] **Step 1: Write failing tests**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
  test(`keeps graph accessible at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await installWorkbenchMocks(page, { stepIndex: 3 })
    await page.goto('/process/quick?express=1&workflowId=w1')
    await page.keyboard.press('Tab')
    await expect(page.locator(':focus')).toBeVisible()
    await expect(page.getByRole('list', { name: /Graph nodes|圖譜節點/ })).toContainText('node-7')
    await expect(page.getByTestId('persistent-rag-graph')).toHaveAttribute('data-reduced-motion', 'true')
  })
}

test('preserves the last graph on workflow failure', async ({ page }) => {
  await installWorkbenchMocks(page, { stepIndex: 3, failRoute: 'workflow' })
  await page.goto('/process/quick?express=1&workflowId=w1')
  await expect(page.getByTestId('workflow-error')).toBeVisible()
  await expect(page.getByTestId('graph-node-node-7')).toBeVisible()
  await expect(page.getByRole('button', { name: /Retry|重試/ })).toBeVisible()
})
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npx playwright test tests/e2e/workbench-accessibility.spec.js tests/e2e/workbench-failures.spec.js`

- [ ] **Step 3: Implement states and translations**

No new hardcoded Chinese/English. Use `aria-live` for progress, buttons for toggles, `aria-pressed` where applicable. Reduce Motion stops decorative graph animation but does not disable data updates.

The failure-state `Retry` button must call workflow action `retry_current_step` and remain disabled until the server returns the new queued workflow revision; it must not rerun a local callback or mutate the visible step.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
cd frontend
npm run typecheck
npm run build
npx playwright test tests/e2e/workbench-accessibility.spec.js tests/e2e/workbench-failures.spec.js
```

Commit: `fix: harden workbench accessibility and failures`

### Task 18: Final integration, provenance and reviewer gates

**Files:**
- Modify: `docs/upstream/mirofish-reuse-audit.md`
- Modify: `THIRD_PARTY_NOTICES.md`, `NOTICE`, `README.md`, `package.json`, `frontend/package.json`, `pyproject.toml` so each exactly matches the final reuse ledger branch from Task 1
- Modify: `frontend/tests/e2e/process-smoke.spec.js`
- Create: `frontend/tests/e2e/guided-workflow.spec.js`
- Modify: `reports/project_dashboard.html`

**Interfaces:**
- Produces: verified five-step journey, final source provenance, project dashboard, review package.

- [ ] **Step 1: Add complete guided journey test**

```js
import { expect, test } from '@playwright/test'
import { installWorkbenchMocks } from './helpers/workbenchMocks.js'

test('completes the five-step guided journey', async ({ page }) => {
  await installWorkbenchMocks(page, { autoAdvance: true, credibility: 'model_estimate' })
  await page.goto('/process/quick')
  const graph = page.getByTestId('persistent-rag-graph')
  const graphInstance = await graph.getAttribute('data-instance-id')
  for (const step of [1, 2, 3, 4, 5]) {
    await expect(page.getByTestId('workflow-step')).toHaveText(String(step).padStart(2, '0'))
    await expect(graph).toHaveAttribute('data-instance-id', graphInstance)
    if (step < 5) {
      await expect(page.getByTestId('primary-step-action')).toHaveCount(1)
      await page.getByTestId('primary-step-action').click()
    }
  }
  await expect(page.getByTestId('interaction-targets')).toBeVisible()
})
```

- [ ] **Step 2: Run backend verification**

```bash
make test-all
```

Expected: zero failures, including slow non-integration and integration tests. Record exact counts and elapsed time in the dashboard; do not reuse earlier counts.

- [ ] **Step 3: Run frontend verification**

```bash
cd frontend
npm run typecheck
npm run build
npx playwright test
```

Expected: zero failures. Inspect desktop/mobile screenshots for clipping, blank graph, focus loss and unlocalized strings.

- [ ] **Step 4: Audit provenance and file sizes**

```bash
git diff --check
find frontend/src -name '*.vue' -print0 | xargs -0 wc -l | sort -nr | head -25
rg -n 'MiroFish|b5b53acc57189a4a42e44a23e149dc655c98fe82|SPDX-License-Identifier' frontend/src docs/upstream THIRD_PARTY_NOTICES.md NOTICE
rg -n 'model_fit=0\.7|confidence_score: float = 0\.5|confidence_level: str = "medium"' backend frontend
```

Expected: touched Vue files ≤800 lines; every copied/adapted file appears in ledger/notices; forbidden fake defaults absent.

- [ ] **Step 5: Remove transient verification outputs**

Resolve exact disposable files first, then remove only these project outputs: `.pytest_cache/`, repository `__pycache__/`, `frontend/dist/`, `frontend/test-results/`, `frontend/playwright-report/`, and generated benchmark result JSONs matching `data/benchmarks/*_latest.json` or timestamped `data/benchmarks/*_YYYY*.json`. Preserve `data/benchmarks/fixtures/` and intentional seed files. Re-run `git status --short` and confirm no source or fixture was removed.

- [ ] **Step 6: Terra independent review**

Provide Terra the spec, this plan, merge-base→HEAD review package, fresh test outputs and reuse ledger. Terra must issue separate verdicts for correctness, scientific claims, UI regression, accessibility, licensing/provenance and scope. Fix all Critical/Important findings and re-run covering tests.

- [ ] **Step 7: Sol whole-branch inspection**

After Terra is clean, provide Sol the same artifacts plus Terra verdict/fix evidence. Sol verifies all acceptance criteria and no later phase remains.

- [ ] **Step 8: Update dashboard and commit**

Update `reports/project_dashboard.html` with verified metrics, risks, reviewer verdicts and any remaining non-blocking limitations.

Commit: `test: verify guided RAG workbench end to end`

---

## Phase gates and session boundaries

1. Phase 0 must finish before any upstream code is copied.
2. Phase A must finish before new credibility UI is exposed.
3. Phase B must finish before any Step component integration.
4. Phase C must finish before report/interaction visual reuse.
5. After each phase, run `$phase-handoff`; the next fresh session starts only the immediate next phase.
6. Preferred executor is Luna 5.6 when the new Codex session exposes it. If the session cannot select Luna, state the actual available model and stop for user direction instead of claiming Luna was used.
7. Terra does not edit during independent review unless explicitly dispatched as a fixer after returning findings.
8. Sol owns initial architecture and final whole-branch inspection; executor self-review never replaces Terra/Sol gates.
