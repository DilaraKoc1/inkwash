import hashlib


def keyed_uniform(key: str, prev_token: int, token: int) -> float:
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

    # Requirement 4: uniformly distributed
    gamma = 0.25
    n = 100_000
    green = sum(keyed_uniform("secret", 42, t) < gamma for t in range(n))
    print(f"green fraction: {green / n:.4f}  (expected ~{gamma})")