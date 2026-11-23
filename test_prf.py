"""Tests for prf.keyed_uniform. Run with: python -m pytest"""

import math

from prf import CHECK_PREV_TOKENS, keyed_uniform

KEY = "secret"


def test_deterministic():
    """Requirement 1: the same inputs always give the same number."""
    assert keyed_uniform(KEY, 42, 1337) == keyed_uniform(KEY, 42, 1337)


def test_different_key_gives_different_number():
    """Requirement 2: a different key gives a different number."""
    assert keyed_uniform(KEY, 42, 1337) != keyed_uniform("other-key", 42, 1337)


def test_different_context_gives_different_number():
    """Requirement 3: a different previous token gives a different number."""
    assert keyed_uniform(KEY, 42, 1337) != keyed_uniform(KEY, 43, 1337)


def test_result_is_in_unit_interval():
    """Every number lies in [0, 1)."""
    for token in range(10_000):
        value = keyed_uniform(KEY, 42, token)
        assert 0.0 <= value < 1.0, f"token {token} gave {value}"


def test_uniform_for_several_previous_tokens():
    """Requirement 4: about gamma of all tokens are green, for every context."""
    gamma = 0.25
    n = 100_000
    # Standard deviation of the green fraction if the numbers are uniform.
    sigma = math.sqrt(gamma * (1 - gamma) / n)
    # 5 sigma: a correct function fails this only about once in 1.7 million.
    tolerance = 5 * sigma

    for prev in CHECK_PREV_TOKENS:
        green = sum(keyed_uniform(KEY, prev, t) < gamma for t in range(n))
        fraction = green / n
        assert abs(fraction - gamma) < tolerance, (
            f"prev token {prev}: {fraction:.2%} green, "
            f"expected {gamma:.0%} ± {tolerance:.2%}"
        )
