"""Session observations, without manufacturing forecast confidence."""
from fastapi import APIRouter

from backend.app.utils.db import get_db

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/{session_id}")
async def get_validation(session_id: str) -> dict:
    async with get_db() as db:
        rows = await (await db.execute(
            "SELECT metric_name, p25, p50, p75, n_trials FROM ensemble_results "
            "WHERE session_id=? ORDER BY id DESC LIMIT 20", (session_id,),
        )).fetchall()
        count = await (await db.execute(
            "SELECT COUNT(*) FROM agent_decisions WHERE session_id=?", (session_id,),
        )).fetchone()
    return {
        "confidence_score": None,
        "confidence_level": "unverified",
        "credibility_tier": "scenario_exploration",
        "backtest_vs_naive": None,
        "backtest_vs_arima": None,
        "mc_band_width": None,
        "agent_consensus": None,
        "sensitivity_score": None,
        "explanation_zh": "目前只有模型內的模擬結果，未有適用於此情境的預測驗證。",
        "missing_evidence": ["claim_scoped_backtest", "calibration"],
        "decision_count": count[0] if count else 0,
        "simulation_distributions": [dict(row) for row in rows],
    }
