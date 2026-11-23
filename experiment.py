"""Toy experiment: how delta and entropy change the strength of the watermark."""

import math
import time

import numpy as np

from green_list import apply_watermark, colour_tokens, detect


THRESHOLD = 4.0  # z-score above which a text counts as watermarked


def softmax(scores: np.ndarray) -> np.ndarray:
    """Turn scores into probabilities that add up to 1."""
    highest = scores.max()
    shifted = scores - highest  # the largest value becomes 0, so exp cannot overflow
    exp_values = np.exp(shifted)
    total = exp_values.sum()
    probs = exp_values / total
    return probs


def generate_toy(key: str, length: int, vocab_size: int,
                 delta: float, sharpness: float, rng: np.random.Generator) -> list[int]:
    """Sample a sequence of token ids from a random toy model with the watermark applied."""
    first_token = int(rng.integers(vocab_size))
    token_ids = [first_token]

    while len(token_ids) < length:
        previous_token = token_ids[-1]

        # 1. The toy model gives every token a random score.
        scores = rng.normal(0, sharpness, vocab_size)

        # 2. Green tokens get a bonus of delta.
        scores = apply_watermark(scores, key, previous_token, delta=delta)

        # 3. Scores become probabilities.
        probs = softmax(scores)

        # 4. Draw the next token according to these probabilities.
        next_token = int(rng.choice(vocab_size, p=probs))
        token_ids.append(next_token)

    return token_ids


def measure(key: str, delta: float, sharpness: float, n_texts: int,
            rng: np.random.Generator, length: int = 200, vocab_size: int = 1000) -> dict:
    """Generate n_texts toy texts with the same settings and summarise how the detector scores them."""
    if n_texts < 1:
        raise ValueError(f"n_texts must be at least 1, got {n_texts}")

    green_fractions = []
    z_scores = []

    for _ in range(n_texts):
        token_ids = generate_toy(key, length, vocab_size, delta, sharpness, rng)
        result = detect(key, token_ids)
        green_fractions.append(result["green_fraction"])
        z_scores.append(result["z"])

    # Average share of green tokens
    green_mean = sum(green_fractions) / len(green_fractions)

    # Average z-score
    z_mean = sum(z_scores) / len(z_scores)

    # Standard deviation of the z-scores: how much they vary around the average
    squared_distances = 0
    for z in z_scores:
        squared_distances += (z - z_mean) ** 2
    z_std = math.sqrt(squared_distances / len(z_scores))

    # Share of texts the detector recognises
    detected = 0
    for z in z_scores:
        if z > THRESHOLD:
            detected += 1
    detection_rate = detected / len(z_scores)

    summary = {}
    summary["green_mean"] = green_mean
    summary["z_mean"] = z_mean
    summary["z_std"] = z_std
    summary["detection_rate"] = detection_rate
    return summary


if __name__ == "__main__":
    start = time.perf_counter()
    key = "secret"
    rng = np.random.default_rng(0)

    print("sharpness  delta  green  z mean  z std  detected")
    for sharpness in [0.5, 2.0, 5.0]:
        for delta in [0.0, 1.0, 2.0, 4.0]:
            summary = measure(key, delta, sharpness, n_texts=20, rng=rng)

            green = f"{summary['green_mean']:>5.0%}"
            z_mean = f"{summary['z_mean']:>6.1f}"
            z_std = f"{summary['z_std']:>5.1f}"
            detected = f"{summary['detection_rate']:>8.0%}"
            print(f"{sharpness:>9}  {delta:>5}  {green}  {z_mean}  {z_std}  {detected}")

    example = generate_toy(key, length=20, vocab_size=1000,
                           delta=2.0, sharpness=0.5, rng=rng)
    colours = colour_tokens(key, example)

    print(f"{example[0]:>4}  (start, no colour)")
    # example[1:] skips the first token, so both lists line up: colours[0] belongs to example[1]
    for token_id, colour in zip(example[1:], colours):
        print(f"{token_id:>4}  {colour}")

    duration = time.perf_counter() - start
    print(f"took {duration:.1f} s")
