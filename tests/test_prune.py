import itertools

import pytest

from stridecoach.cost import prune_conversation_history


def alternating(n, start="user"):
    other = "assistant" if start == "user" else "user"
    return [{"role": start if i % 2 == 0 else other, "content": f"turn {i}"} for i in range(n)]


def test_short_history_is_returned_unchanged():
    history = alternating(3)
    assert prune_conversation_history(history, keep_last_n=4) == history


@pytest.mark.parametrize(("keep", "n"), [(k, n) for k in (1, 2, 4, 6) for n in range(k + 1, 15)])
@pytest.mark.parametrize("start", ["user", "assistant"])
def test_roles_keep_alternating_after_pruning(n, keep, start):
    history = alternating(n, start=start)
    pruned = prune_conversation_history(history, keep_last_n=keep)
    roles = [m["role"] for m in pruned]
    assert all(a != b for a, b in itertools.pairwise(roles)), roles
    assert pruned[-keep:] == history[-keep:]


def test_older_turns_become_one_history_summary():
    history = alternating(8)
    pruned = prune_conversation_history(history, keep_last_n=4)
    assert pruned[0]["role"] == "user"
    assert pruned[0]["content"].startswith("<history_summary>")
    assert "turn 0" in pruned[0]["content"]
    assert "turn 3" in pruned[0]["content"]
    assert "turn 4" not in pruned[0]["content"]


def test_block_style_content_is_digested_by_text_only():
    blocks = [SimpleNamespaceBlock("thinking", None), SimpleNamespaceBlock("text", "visible words")]
    history = [{"role": "assistant", "content": blocks}] + alternating(4, start="user")
    pruned = prune_conversation_history(history, keep_last_n=2)
    assert "visible words" in pruned[0]["content"]
    assert "None" not in pruned[0]["content"]


def test_keep_last_n_must_be_positive():
    with pytest.raises(ValueError):
        prune_conversation_history(alternating(4), keep_last_n=0)


class SimpleNamespaceBlock:
    def __init__(self, type_, text):
        self.type = type_
        self.text = text
