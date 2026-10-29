from __future__ import annotations

from types import SimpleNamespace

from http_packets import decoded_events, ingress
from output_helpers import forward_output

import resin
from resin import Engine
from resin._resin import _HttpSession


class RecordingRunner:
    def __init__(self) -> None:
        self.plans = []

    def forward(self, plan):
        self.plans.append(plan)
        return forward_output([3] * plan.num_sequences)


class LabelRecipe:
    tokenizer = None
    stop_token_ids = []

    def render(self, messages, *, tools=(), options=None):
        label = messages[0].content[0].text
        return resin.recipe.RenderedPrompt([{"low": 10, "high": 20}[label]])

    def create_parser(self, prompt):
        return SimpleNamespace(feed=lambda ids: [resin.recipe.TextDelta("ok")])


def admission(request_id, label, *, priority=None):
    request = {
        "id": request_id,
        "model": "test",
        "messages": [{"role": "user", "content": label}],
        "tools": [],
        "max_output_tokens": 1,
        "temperature": 1.0,
        "top_p": 1.0,
        "top_k": None,
        "seed": None,
        "logprobs": False,
        "top_logprobs": 0,
        "prompt_logprobs": False,
        "routed_dp_rank": None,
        "stop": [],
        "reasoning_effort": None,
        "extra": {},
    }
    if priority is not None:
        request["priority"] = priority
    return ingress([request])


def test_http_session_admits_higher_priority_requests_first() -> None:
    runner = RecordingRunner()
    engine = Engine(runner, max_running_requests=1)
    session = _HttpSession(engine, LabelRecipe())
    session.admit(admission("low", "low", priority=0))
    session.admit(admission("high", "high", priority=5))

    first = decoded_events(session.process(engine.step()))
    assert runner.plans[-1].token_ids.tolist() == [20]
    assert [
        request_id for request_id, event in first if event["type"] == "finished"
    ] == ["high"]

    second = decoded_events(session.process(engine.step()))
    assert runner.plans[-1].token_ids.tolist() == [10]
    assert [
        request_id for request_id, event in second if event["type"] == "finished"
    ] == ["low"]
    engine.close()


def test_http_session_omitted_priority_matches_explicit_zero() -> None:
    runner = RecordingRunner()
    engine = Engine(runner, max_running_requests=1)
    session = _HttpSession(engine, LabelRecipe())
    session.admit(admission("omitted", "low"))
    session.admit(admission("zero", "high", priority=0))

    first = decoded_events(session.process(engine.step()))
    assert runner.plans[-1].token_ids.tolist() == [10]
    assert [
        request_id for request_id, event in first if event["type"] == "finished"
    ] == ["omitted"]
    second = decoded_events(session.process(engine.step()))
    assert runner.plans[-1].token_ids.tolist() == [20]
    assert [
        request_id for request_id, event in second if event["type"] == "finished"
    ] == ["zero"]
    engine.close()
