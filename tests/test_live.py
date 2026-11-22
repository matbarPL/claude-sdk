import os

import pytest

from stridecoach.coach_api import StrideCoachAPI

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the API"),
]


def test_one_short_real_call_ends_cleanly():
    api = StrideCoachAPI()
    _, result = api.ask_coach([{"role": "user", "content": "Reply with one short encouraging sentence."}], max_tokens=60)
    assert result.stop_reason in {"end_turn", "max_tokens"}
    assert result.request_id is not None
    assert result.text and not result.text.startswith("[")
