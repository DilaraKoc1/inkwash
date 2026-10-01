import hashlib


def keyed_uniform(key: str, prev_token: int, token: int) -> float:
    message = f"{key} | {prev_token} | {token}"
    digest = hashlib.sha256(message.encode()).digest()
    number = int.from_bytes(digest[:8], "big")
    return number / 2**64


if __name__ == "__main__":
    # Anforderung 1: deterministisch
    a = keyed_uniform("geheim", 42, 1337)
    b = keyed_uniform("geheim", 42, 1337)
    print("deterministisch:", a == b, a)

    # Anforderung 2: anderer Schlüssel -> andere Zahl
    c = keyed_uniform("anderer-key", 42, 1337)
    print("anderer Schlüssel:", c)

    # Anforderung 3: anderer Kontext -> andere Zahl
    d = keyed_uniform("geheim", 43, 1337)
    print("anderer Kontext:", d)

    # Anforderung 4: gleichmäßig verteilt
    gamma = 0.25
    n = 100_000
    green = sum(keyed_uniform("geheim", 42, t) < gamma for t in range(n))
    print(f"Anteil grün: {green / n:.4f}  (erwartet ~{gamma})")