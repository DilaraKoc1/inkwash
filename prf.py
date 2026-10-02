"""Keyed pseudo-random function: the source of randomness for the green list."""

import hashlib


def keyed_uniform(key: str, prev_token: int, token: int) -> float:
    """Return a number in [0, 1) that depends on the key, the previous token and the token.

    The same inputs always give the same number. Without the key the numbers
    look random, and they are spread evenly between 0 and 1.
    """
    message = f"{key} | {prev_token} | {token}"
    digest = hashlib.sha256(message.encode()).digest()
    number = int.from_bytes(digest[:8], "big")
    return number / 2**64


if __name__ == "__main__":
    # Requirement 1: deterministic
    a = keyed_uniform("secret", 42, 1337)
    b = keyed_uniform("secret", 42, 1337)
    print("deterministic:", a == b, a)

    # Requirement 2: different key -> different number
    c = keyed_uniform("other-key", 42, 1337)
    print("different key:", c)

    # Requirement 3: different context -> different number
    d = keyed_uniform("secret", 43, 1337)
    print("different context:", d)

    # Requirement 4: uniformly distributed, for several previous tokens
    gamma = 0.25
    n = 100_000
    prev_tokens = [42, 13, 279, 785, 8251, 5517, 389, 1000, 50000, 151000]
    fractions = []
    for prev in prev_tokens:
        green = sum(keyed_uniform("secret", prev, t) < gamma for t in range(n))
        fractions.append(green / n)
        print(f"prev token {prev:>6}: {green:,} of {n:,} green ({green / n:.2%})")
    print(f"range: {min(fractions):.2%} to {max(fractions):.2%}, "
          f"average {sum(fractions) / len(fractions):.2%}  (expected ~{gamma:.0%})")
