"""Toy experiment: how delta and entropy change the strength of the watermark."""

import numpy as np

from green_list import apply_watermark, colour_tokens, detect


def softmax(logits: np.ndarray) -> np.ndarray:
    """Turn scores into probabilities that add up to 1."""
    exp = np.exp(logits - logits.max())
    return exp / exp.sum()


def generate_toy(key: str, length: int, vocab_size: int,
                 delta: float, sharpness: float, rng: np.random.Generator) -> list[int]:
    """Sample a sequence of token ids from a random toy model with the watermark applied."""
    token_ids = [int(rng.integers(vocab_size))]
    while len(token_ids) < length:
        logits = rng.normal(0, sharpness, vocab_size)
        logits = apply_watermark(logits, key, token_ids[-1], delta=delta)
        probs = softmax(logits)
        token_ids.append(int(rng.choice(vocab_size, p=probs)))
    return token_ids


if __name__ == "__main__":
    key = "secret"
    rng = np.random.default_rng(0)

    for sharpness in [0.5, 2.0, 5.0]:
        for delta in [0.0, 1.0, 2.0, 4.0]:
            token_ids = generate_toy(key, length=200, vocab_size=1000,
                                     delta=delta, sharpness=sharpness, rng=rng)
            result = detect(key, token_ids)
            print(f"sharpness={sharpness:<4} delta={delta:<4} "
                  f"green={result['green_fraction']:.2f}  z={result['z']:5.1f}")

    example = generate_toy(key, length=20, vocab_size=1000,
                           delta=2.0, sharpness=0.5, rng=rng)
    colours = colour_tokens(key, example)
    print(f"{example[0]:>4}  (start, no colour)")
    for token_id, colour in zip(example[1:], colours):
        print(f"{token_id:>4}  {colour}")