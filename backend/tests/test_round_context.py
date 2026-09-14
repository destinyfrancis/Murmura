"""Offline tests of native OASIS visibility plus Murmura round-state feedback."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.scripts.round_context import CognitiveEnvironment, prepare_round, publish_context


@pytest.mark.asyncio
async def test_private_state_is_previous_round_and_does_not_broadcast(tmp_path):
    alice = SimpleNamespace(env=CognitiveEnvironment(SimpleNamespace(), 'alice', {}))
    bob = SimpleNamespace(env=CognitiveEnvironment(SimpleNamespace(), 'bob', {}))
    graph = SimpleNamespace(get_agents=lambda: [(0, alice), (1, bob)])
    state = SimpleNamespace(
        all_agent_dicts=[{'id': 1, 'name': 'alice'}, {'id': 2, 'name': 'bob'}],
        agent_beliefs={'1': {'trust': 0.2}, '2': {'trust': 0.8}},
        agent_strategies={}, emotional_states={},
    )
    publish_context(str(tmp_path), 1, state)
    await prepare_round(graph, {'round_context_dir': str(tmp_path)}, 2)
    assert alice.env.private_state['beliefs']['trust'] == 0.2
    assert bob.env.private_state['beliefs']['trust'] == 0.8
    assert bob.env.completed_round == 1
    with pytest.raises(TimeoutError):
        await prepare_round(graph, {'round_context_dir': str(tmp_path), 'round_context_timeout_s': 0}, 3)


@pytest.mark.asyncio
async def test_native_oasis_post_reaches_model_input_only_when_visible(tmp_path, monkeypatch):
    # Keep the actual OASIS platform, SQLite, actions, environment and perception.
    # Only the model response is replaced. This proves wiring, not emergence.
    import socket
    monkeypatch.setattr(socket.socket, 'connect', lambda *a: pytest.fail('Offline test attempted network'))
    import oasis
    from camel.models import StubModel
    from camel.types import ModelType
    from backend.scripts.round_context import attach_context

    csv = tmp_path / 'agents.csv'
    csv.write_text('user_id,name,username,user_char,description\n0,Alice,alice,curious,Actor A\n1,Bob,bob,cautious,Actor B\n')
    graph = await oasis.generate_twitter_agent_graph(
        profile_path=str(csv), model=StubModel(ModelType.STUB),
        available_actions=[oasis.ActionType.CREATE_POST, oasis.ActionType.FOLLOW],
    )
    env = oasis.make(agent_graph=graph, platform=oasis.DefaultPlatformType.TWITTER,
                     database_path=str(tmp_path / 'oasis.db'))
    await env.reset()
    try:
        alice, bob = [agent for _, agent in graph.get_agents()]
        await alice.env.action.create_post('The bridge is closed: choose the ferry.')
        await bob.env.action.follow(alice.social_agent_id)
        config = {'round_context_dir': str(tmp_path / 'context'), 'seed_text': 'A village faces a flood.'}
        attach_context(graph, config)
        publish_context(config['round_context_dir'], 0, None)
        await prepare_round(graph, config, 1)
        bob.astep = AsyncMock(return_value=SimpleNamespace(info={'tool_calls': []}))
        await bob.perform_action_by_llm()
        observed = bob.astep.call_args.args[0].content
        assert 'choose the ferry' in observed
        assert 'A village faces a flood' in observed

        # Remove B's actual feed/follow access, leaving A's post stored.
        env.platform.db_cursor.execute('DELETE FROM follow')
        env.platform.db_cursor.execute('DELETE FROM rec')
        await bob.perform_action_by_llm()
        assert 'choose the ferry' not in bob.astep.call_args.args[0].content
    finally:
        await env.close()


@pytest.mark.asyncio
async def test_real_subprocess_waits_for_parent_and_persists_both_rounds(tmp_path, test_client, monkeypatch):
    """Use the shipping Twitter loop/IPC/SQLite with offline scripted model actions.

    Cognition is controlled here to test the acknowledgement boundary; its
    model quality is deliberately outside this test's claim.
    """
    import asyncio
    import json
    import sys
    from pathlib import Path
    from backend.app.models.kg_session_state import KGSessionState
    from backend.app.services.simulation_runner import SimulationRunner
    from backend.app.services.demo_replay import DEMO_SESSION_ID, ensure_demo_replay
    from backend.app.utils.db import get_db
    from backend.app.services import simulation_lifecycle, simulation_helpers

    await ensure_demo_replay()
    root = Path(__file__).resolve().parents[2]
    wrapper = tmp_path / 'offline_oasis.py'
    wrapper.write_text(f'''
import sys, socket, json
from types import SimpleNamespace
sys.path.insert(0, {str(root)!r})
sys.path.insert(0, {str(root / 'backend/scripts')!r})
def no_network(*args):
    raise RuntimeError('Offline subprocess attempted network')
socket.socket.connect = no_network
from camel.models import StubModel
from camel.types import ModelType
from oasis.social_agent.agent import SocialAgent
import run_twitter_simulation as script
script.build_model = lambda config: StubModel(ModelType.STUB)
async def scripted_step(self, message, *args, **kwargs):
    round_num = self.env.round_number
    if round_num == 2:
        assert 'parent_acknowledged' in message.content, message.content
    await self.env.action.create_post(f'OFFLINE_PROOF round {{round_num}} actor {{self.social_agent_id}}')
    return SimpleNamespace(info={{'tool_calls': []}})
SocialAgent.astep = scripted_step
script.main()
''')
    csv = tmp_path / 'actors.csv'
    csv.write_text('user_id,name,username,user_char,description\n0,Alice,alice,curious,Actor A\n1,Bob,bob,cautious,Actor B\n')
    monkeypatch.setattr(simulation_lifecycle, '_SCRIPT_PATH', wrapper)
    monkeypatch.setattr(simulation_lifecycle, '_PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(simulation_helpers, '_PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(simulation_lifecycle, '_PYTHON_BIN', Path(sys.executable))
    monkeypatch.setattr(simulation_helpers, '_get_api_key', lambda: '')
    runner = SimulationRunner()
    state = KGSessionState(all_agent_dicts=[{'id': '0', 'name': 'alice'}, {'id': '1', 'name': 'bob'}])

    async def initialise(*args):
        runner._kg_sessions[DEMO_SESSION_ID] = state

    async def cognition(session_id, round_number):
        await asyncio.sleep(0.05)
        state.agent_beliefs = {'0': {'parent_acknowledged': round_number}, '1': {'parent_acknowledged': round_number}}

    monkeypatch.setattr(runner, '_init_kg_driven_mode', initialise)
    monkeypatch.setattr(runner, '_restore_macro_state', AsyncMock(return_value=None))
    monkeypatch.setattr(runner, '_load_activity_profiles', lambda *args: None)
    monkeypatch.setattr(runner, '_is_agent_active', lambda *args: True)
    for method in ('_run_bias_probe', '_init_multi_layer_network', '_process_kg_snapshot', '_generate_emergence_scorecard'):
        monkeypatch.setattr(runner, method, AsyncMock())
    hooks = AsyncMock(side_effect=cognition)
    monkeypatch.setattr(runner, '_execute_round_hooks', hooks)
    await asyncio.wait_for(runner.run(DEMO_SESSION_ID, {
        'agent_csv_path': str(csv), 'round_count': 2, 'agent_count': 2,
        'platforms': {'twitter': True}, 'preset': 'research', 'seed_text': 'Offline flood scenario.',
        'round_context_timeout_s': 5,
    }), timeout=35)
    assert [call.args[1] for call in hooks.call_args_list] == [1, 2]
    async with get_db() as db:
        rows = await (await db.execute(
            "SELECT round_number, content FROM simulation_actions WHERE session_id=? AND content LIKE 'OFFLINE_PROOF%'",
            (DEMO_SESSION_ID,),
        )).fetchall()
    assert {row['round_number'] for row in rows} == {1, 2}
    assert len(rows) >= 4
    config = json.loads((tmp_path / 'data/sessions' / DEMO_SESSION_ID / 'sim_config.json').read_text())
    assert Path(config['round_context_dir'], '2.json').exists()
