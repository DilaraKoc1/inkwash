import math

from prf import keyed_uniform


def is_green(key: str, prev_token: int, token: int, gamma: float = 0.25) -> bool:
    return keyed_uniform(key, prev_token, token) < gamma


def detect(key: str, token_ids: list[int], gamma: float = 0.25) -> dict:
    green = 0
    n = 0
    for i in range(1, len(token_ids)):
        prev_token = token_ids[i - 1]
        token = token_ids[i]
        if is_green(key, prev_token, token, gamma):
            green += 1
        n += 1
    expected = n * gamma
    std = math.sqrt(n * gamma * (1 - gamma))
    z = (green - expected) / std
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
