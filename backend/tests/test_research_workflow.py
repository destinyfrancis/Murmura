"""Offline product checks through existing API/SQLite, not live model claims."""
import pytest


@pytest.mark.asyncio
async def test_scripted_replay_can_open_graph_actions_and_report_without_login(test_client):
    from backend.app.services.demo_replay import DEMO_SESSION_ID, ensure_demo_replay
    await ensure_demo_replay()
    await ensure_demo_replay()  # restarting must not duplicate the example
    session = (await test_client.get(f"/api/simulation/{DEMO_SESSION_ID}")).json()["data"]
    assert session["report_id"] == "murmura-scripted-flood-report"
    graph = (await test_client.get(f"/api/graph/{DEMO_SESSION_ID}")).json()["data"]
    assert len(graph["nodes"]) == 3
    evidence = await test_client.get(f"/api/graph/{DEMO_SESSION_ID}/node/demo_ling/evidence")
    assert evidence.status_code == 200
    assert '預先編寫' in evidence.json()['data']['source_texts'][0]
    confidence = await test_client.get(f"/api/simulation/{DEMO_SESSION_ID}/confidence-report")
    assert confidence.status_code == 200
    assert confidence.json()['data']['overall_score'] is None
    actions = (await test_client.get(f"/api/simulation/{DEMO_SESSION_ID}/actions?latest=true&limit=1")).json()["data"]
    assert len(actions) == 1 and actions[0]["round_number"] == 3
    report = await test_client.get(f"/api/report/{session['report_id']}")
    assert report.status_code == 200
    assert "沒有呼叫模型" in report.json()["data"]["content_markdown"]
    validation = await test_client.get(f"/api/validation/{DEMO_SESSION_ID}")
    assert validation.status_code == 200
    assert validation.json()["confidence_score"] is None


@pytest.mark.asyncio
async def test_local_report_cites_choices_and_excludes_search_payloads(test_client):
    from backend.app.services.demo_replay import DEMO_SESSION_ID, ensure_demo_replay
    from backend.app.utils.db import get_db
    await ensure_demo_replay()
    async with get_db() as db:
        await db.execute(
            "INSERT INTO agent_decisions (session_id,agent_id,round_number,decision_type,action,reasoning) "
            "VALUES (?,1,3,'fuel','advance_payment','先救病人')", (DEMO_SESSION_ID,),
        )
        await db.execute(
            "INSERT INTO simulation_actions (session_id,agent_id,oasis_username,round_number,action_type,platform,content) "
            "VALUES (?,1,'searcher',3,'search_posts','twitter','SECRET_SEARCH_PAYLOAD')", (DEMO_SESSION_ID,),
        )
        await db.commit()
    result = await test_client.post('/api/report/generate', json={
        'session_id': DEMO_SESSION_ID, 'report_type': 'grounded',
        'scenario_question': '角色如何處理燃料短缺？',
    })
    assert result.status_code == 200
    content = result.json()['data']['content_markdown']
    assert 'advance_payment' in content and '[agent_decisions:' in content
    assert 'SECRET_SEARCH_PAYLOAD' not in content
    assert '未量度其他結局的機率' in content


@pytest.mark.asyncio
async def test_generic_monte_carlo_has_no_invented_future_bands():
    from backend.app.services.monte_carlo import MonteCarloEngine
    result = await MonteCarloEngine()._run_generic_ensemble('unvalidated', ['trust'], 500)
    assert result.n_trials == 0
    assert result.distributions == []
    assert result.to_dict()['data_integrity_score'] is None


@pytest.mark.asyncio
async def test_research_cast_does_not_invent_background_people(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from backend.app.services.kg_agent_factory import KGAgentFactory
    factory = KGAgentFactory(llm_client=MagicMock())
    nodes = [{'id': 'a', 'title': 'Alice', 'entity_type': 'Person'},
             {'id': 'b', 'title': 'Bob', 'entity_type': 'Person'}]
    monkeypatch.setattr(factory, '_filter_agent_eligible_nodes', AsyncMock(return_value=nodes))
    monkeypatch.setenv('KG_AGENT_STRICT_TEMPLATE_PROFILES', '1')
    profiles = await factory.generate_from_kg(nodes, [], 'Alice and Bob discuss moving.',
                                               target_count=16, expand_background=False)
    assert len(profiles) == 2
    assert {p.kg_node_id for p in profiles} == {'a', 'b'}
