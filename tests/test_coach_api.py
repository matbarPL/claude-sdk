from types import SimpleNamespace

import pytest

from stridecoach.coach_api import MAX_TOKENS_CAP, StrideCoachAPI


def fake_message(stop_reason="end_turn", content=(), request_id="req_test"):
    usage = SimpleNamespace(input_tokens=12, output_tokens=7)
    return SimpleNamespace(stop_reason=stop_reason, content=list(content), usage=usage, _request_id=request_id)


def block(type_, text=None):
    return SimpleNamespace(type=type_, text=text)


def test_plain_text_response_is_validated():
    result = StrideCoachAPI.validate_response(fake_message(content=[block("text", "Good tempo.")]))
    assert result.text == "Good tempo."
    assert result.stop_reason == "end_turn"
    assert result.request_id == "req_test"
    assert (result.input_tokens, result.output_tokens) == (12, 7)
    assert not result.is_truncated and not result.is_refusal


def test_text_is_found_after_a_non_text_block():
    msg = fake_message(content=[block("thinking"), block("text", "Found me.")])
    assert StrideCoachAPI.validate_response(msg).text == "Found me."


def test_refusal_is_flagged_before_content_is_read():
    result = StrideCoachAPI.validate_response(fake_message(stop_reason="refusal", content=[block("text", "x")]))
    assert result.is_refusal
    assert result.text.startswith("[REFUSAL]")


def test_empty_content_is_guarded():
    result = StrideCoachAPI.validate_response(fake_message(content=[]))
    assert result.text.startswith("[EMPTY]")


def test_no_text_blocks_is_reported_not_raised():
    result = StrideCoachAPI.validate_response(fake_message(content=[block("tool_use")]))
    assert "tool_use" in result.text


def test_max_tokens_marks_truncation():
    result = StrideCoachAPI.validate_response(fake_message(stop_reason="max_tokens", content=[block("text", "Half")]))
    assert result.is_truncated
    assert result.text == "Half"


def test_missing_request_id_is_none_not_an_error():
    msg = fake_message(content=[block("text", "ok")])
    del msg._request_id
    assert StrideCoachAPI.validate_response(msg).request_id is None


def test_max_tokens_above_cap_is_rejected_before_any_call():
    api = StrideCoachAPI(client=object())  # any call would fail on this object
    with pytest.raises(ValueError):
        api.ask_coach([{"role": "user", "content": "hi"}], max_tokens=MAX_TOKENS_CAP + 1)
    with pytest.raises(ValueError):
        api.ask_coach([{"role": "user", "content": "hi"}], max_tokens=0)


def test_batch_items_use_pinned_model_and_workout_ids():
    api = StrideCoachAPI(client=object())
    items = api.build_season_backfill_batch(
        [{"workout_id": "run-2026-11-01", "note": "easy"}, {"workout_id": "run-2026-11-08", "note": "long"}]
    )
    assert [i["custom_id"] for i in items] == ["run-2026-11-01", "run-2026-11-08"]
    assert all(i["params"]["model"] == "claude-haiku-4-5-20251001" for i in items)
    assert all(i["params"]["max_tokens"] <= MAX_TOKENS_CAP for i in items)


@pytest.mark.parametrize("bad_id", ["run 2026", "run/2026", "x" * 65, ""])
def test_batch_rejects_invalid_custom_ids(bad_id):
    with pytest.raises(ValueError):
        StrideCoachAPI(client=object()).build_season_backfill_batch([{"workout_id": bad_id, "note": "n"}])


def test_batch_rejects_duplicate_custom_ids():
    workouts = [{"workout_id": "run-1", "note": "a"}, {"workout_id": "run-1", "note": "b"}]
    with pytest.raises(ValueError):
        StrideCoachAPI(client=object()).build_season_backfill_batch(workouts)
