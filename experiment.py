"""Toy experiment: how delta and entropy change the strength of the watermark."""

import time

import numpy as np

from green_list import apply_watermark, colour_tokens, detect


THRESHOLD = 4.0  # z-score above which a text counts as watermarked


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


def measure(key: str, delta: float, sharpness: float, n_texts: int,
            rng: np.random.Generator, length: int = 200, vocab_size: int = 1000) -> dict:
    """Generate n_texts toy texts with the same settings and summarise how the detector scores them."""
    green_fractions = []
    z_scores = []
    for _ in range(n_texts):
        token_ids = generate_toy(key, length, vocab_size, delta, sharpness, rng)
        result = detect(key, token_ids)
        green_fractions.append(result["green_fraction"])
        z_scores.append(result["z"])
    z_scores = np.array(z_scores)
    return {
        "green_mean": float(np.mean(green_fractions)),
        "z_mean": float(np.mean(z_scores)),
        "z_std": float(np.std(z_scores)),
        "detection_rate": float(np.mean(z_scores > THRESHOLD)),
    }


if __name__ == "__main__":
    start = time.perf_counter()
    key = "secret"
    rng = np.random.default_rng(0)

    print("sharpness  delta  green  z mean  z std  detected")
    for sharpness in [0.5, 2.0, 5.0]:
        for delta in [0.0, 1.0, 2.0, 4.0]:
            summary = measure(key, delta, sharpness, n_texts=20, rng=rng)
            print(f"{sharpness:>9}  {delta:>5}  {summary['green_mean']:>5.0%}  "
                  f"{summary['z_mean']:>6.1f}  {summary['z_std']:>5.1f}  {summary['detection_rate']:>8.0%}")

    example = generate_toy(key, length=20, vocab_size=1000,
                           delta=2.0, sharpness=0.5, rng=rng)
    colours = colour_tokens(key, example)
    print(f"{example[0]:>4}  (start, no colour)")
    for token_id, colour in zip(example[1:], colours):
        print(f"{token_id:>4}  {colour}")

    print(f"took {time.perf_counter() - start:.1f} s")