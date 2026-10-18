"""Green-list watermark (Kirchenbauer et al., 2023): colour rule, bonus and detector."""

import math
from functools import lru_cache

import numpy as np

from prf import keyed_uniform


def is_green(key: str, prev_token: int, token: int, gamma: float = 0.25) -> bool:
    """Return True if token is green after prev_token, i.e. its number is below gamma."""
    return keyed_uniform(key, prev_token, token) < gamma


@lru_cache(maxsize=None)
def green_mask(key: str, prev_token: int, vocab_size: int, gamma: float = 0.25) -> np.ndarray:
    """Return a read-only True/False array marking which tokens are green after prev_token.

    The result is cached, so every call with the same arguments gets the same array.
    It is read-only so that no caller can change the green list for everyone else.
    """
    mask = np.array([is_green(key, prev_token, token_id, gamma) for token_id in range(vocab_size)])
    mask.setflags(write=False)
    return mask


def apply_watermark(logits: np.ndarray, key: str, prev_token: int,
                    gamma: float = 0.25, delta: float = 2.0) -> np.ndarray:
    """Return a copy of logits with delta added to every green token."""
    return logits + delta * green_mask(key, prev_token, len(logits), gamma)


def detect(key: str, token_ids: list[int], gamma: float = 0.25) -> dict:
    """Count green tokens in a text and turn the count into a z-score.

    Each pair (previous token, token) is scored once. Without the key, each
    pair is green with chance gamma. A z-score above 4 means the text is
    very unlikely to have been written without the key.

    Returns n (scored pairs), green, green_fraction and z.
    """
    if len(token_ids) < 2:
        raise ValueError("detect needs at least 2 tokens to score one pair")

    green = 0
    n = 0
    for i in range(1, len(token_ids)):
        prev_token = token_ids[i - 1]
        token_id = token_ids[i]
        if is_green(key, prev_token, token_id, gamma):
            green += 1
        n += 1
    expected = n * gamma
    spread = math.sqrt(n * gamma * (1 - gamma))
    z = (green - expected) / spread
    return {"n": n, "green": green, "green_fraction": green / n, "z": z}


def colour_tokens(key: str, token_ids: list[int], gamma: float = 0.25) -> list[str]:
    """Return 'green' or 'red' for each token after the first, as the detector sees it."""
    colours = []
    for i in range(1, len(token_ids)):
        if is_green(key, token_ids[i - 1], token_ids[i], gamma):
            colours.append("green")
        else:
            colours.append("red")
    return colours


if __name__ == "__main__":
    import random

    random.seed(0)
    key = "secret"
    vocab_size = 50_000
    length = 200

    human = [random.randrange(vocab_size) for _ in range(length)]
    print("human:      ", detect(key, human))

    wm = [random.randrange(vocab_size)]
    while len(wm) < length:
        candidate = random.randrange(vocab_size)
        if is_green(key, wm[-1], candidate):
            wm.append(candidate)
    print("watermarked:", detect(key, wm))

    print("wrong key:  ", detect("other-key", wm))
