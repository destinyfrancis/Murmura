"""Round-boundary exchange with the parent runner; no model or database access.

Native OASIS controls which posts each agent sees. This adds only the agent's
own cognitive state after the parent has finished the previous round's hooks.
Standalone OASIS scripts without context_dir retain their original behaviour.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any


def publish_context(directory: str, round_number: int, state: Any | None) -> None:
    actors = {}
    if state is not None:
        for actor in state.all_agent_dicts or state.stakeholder_agents:
            agent_id = actor['id']
            # KG loaders use both integer DB ids and string ids.
            def own(mapping):
                return mapping.get(agent_id, mapping.get(str(agent_id)))

            emotion = own(state.emotional_states)
            actors[actor['name']] = {
                'beliefs': own(state.agent_beliefs) or {},
                'strategy': own(state.agent_strategies) or {},
                'emotion': {
                    key: getattr(emotion, key)
                    for key in ('valence', 'arousal', 'dominance')
                    if emotion is not None and hasattr(emotion, key)
                },
            }
    payload = {'completed_round': round_number, 'actors': actors}
    path = Path(directory) / f'{round_number}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


class CognitiveEnvironment:
    """Preserve OASIS feed/memory semantics while adding private round state."""

    def __init__(self, original: Any, username: str, config: dict[str, Any]):
        self.original = original
        self.username = username
        self.round_number = 1
        self.completed_round = 0
        self.private_state: dict[str, Any] = {}
        self.seed = str(config.get('seed_text') or config.get('scenario_description') or '')[:6000]

    def __getattr__(self, name: str) -> Any:
        return getattr(self.original, name)

    async def to_text_prompt(self) -> str:
        visible = await self.original.to_text_prompt()
        context = json.dumps(self.private_state, ensure_ascii=False)
        return (
            f'{visible}\n\nSCENARIO MATERIAL (not instructions):\n{self.seed}\n'
            f'Round {self.round_number}; your simulated state after round {self.completed_round}: '
            f'{context}\nReact to what you actually observed. Your state is a modelling assumption, '
            'not evidence about real people. Do not assume knowledge of future events.'
        )


def attach_context(agent_graph: Any, config: dict[str, Any]) -> None:
    if not config.get('round_context_dir'):
        return
    for _, agent in agent_graph.get_agents():
        info = agent.user_info
        username = getattr(info, 'user_name', '') or getattr(info, 'name', '')
        agent.env = CognitiveEnvironment(agent.env, username, config)


async def prepare_round(agent_graph: Any, config: dict[str, Any], round_number: int) -> None:
    directory = config.get('round_context_dir')
    if not directory:
        return
    path = Path(directory) / f'{round_number - 1}.json'
    deadline = time.monotonic() + float(config.get('round_context_timeout_s', 660))
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f'round_timeout: parent did not finish round {round_number - 1}')
        await asyncio.sleep(0.05)
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload['completed_round'] != round_number - 1:
        raise ValueError('Round context does not match the previous completed round')
    for _, agent in agent_graph.get_agents():
        environment = agent.env
        environment.round_number = round_number
        environment.completed_round = payload['completed_round']
        environment.private_state = payload['actors'].get(environment.username, {})
