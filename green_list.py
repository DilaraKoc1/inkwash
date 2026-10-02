"""Green-list watermark (Kirchenbauer et al., 2023): colour rule and detector."""

import math

from prf import keyed_uniform


def is_green(key: str, prev_token: int, token: int, gamma: float = 0.25) -> bool:
    """Return True if token is green after prev_token, i.e. its number is below gamma."""
    return keyed_uniform(key, prev_token, token) < gamma


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
        token = token_ids[i]
        if is_green(key, prev_token, token, gamma):
            green += 1
        n += 1
    expected = n * gamma
    spread = math.sqrt(n * gamma * (1 - gamma))
    z = (green - expected) / spread
    return {"n": n, "green": green, "green_fraction": green / n, "z": z}


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
