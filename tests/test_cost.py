from types import SimpleNamespace

import pytest

from stridecoach.cost import calculate_call_cost


def usage(**fields):
    base = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": None, "cache_read_input_tokens": None}
    return SimpleNamespace(**(base | fields))


def test_uncached_call_has_no_savings():
    cost = calculate_call_cost(usage(input_tokens=1_000_000, output_tokens=1_000_000))
    assert cost["total_input_tokens"] == 1_000_000
    assert cost["actual_usd"] == pytest.approx(1.00 + 5.00)
    assert cost["uncached_baseline_usd"] == pytest.approx(6.00)
    assert cost["cache_savings_pct"] == 0.0


def test_cache_read_is_priced_at_tenth_of_input():
    cost = calculate_call_cost(usage(cache_read_input_tokens=1_000_000))
    assert cost["cache_read_tokens"] == 1_000_000
    assert cost["actual_usd"] == pytest.approx(0.10)
    assert cost["uncached_baseline_usd"] == pytest.approx(1.00)
    assert cost["cache_savings_pct"] == pytest.approx(90.0)


def test_cache_write_is_priced_at_1_25x_input():
    cost = calculate_call_cost(usage(input_tokens=100, cache_creation_input_tokens=1_000_000))
    assert cost["total_input_tokens"] == 1_000_100
    assert cost["actual_usd"] == pytest.approx(1.25 + 100 * 1.00 / 1_000_000)
    assert cost["cache_write_tokens"] == 1_000_000


def test_none_usage_fields_count_as_zero():
    cost = calculate_call_cost(usage(input_tokens=10, output_tokens=None))
    assert cost["output_tokens"] == 0
    assert cost["total_input_tokens"] == 10
