"""Keyed pseudo-random function: the source of randomness for the green list."""

import hmac

# Previous tokens used to check that about gamma of all tokens are green.
# 279 is ' the' and 8251 is ' cat' in the Qwen2.5 tokenizer.
CHECK_PREV_TOKENS = [42, 13, 279, 785, 8251, 5517, 389, 1000, 50000, 151000]


def keyed_uniform(key: str, prev_token: int, token: int) -> float:
    """Return a number in [0, 1) that depends on the key, the previous token and the token.

    The same inputs always give the same number. Without the key the numbers
    look random, and they are spread evenly between 0 and 1.
    """
    message = f"{prev_token} | {token}"
    digest = hmac.digest(key.encode(), message.encode(), "sha256")
    # Keep the top 53 bits: a float stores exactly 53, so nothing is rounded
    # and the result can never reach 1.0.
    number = int.from_bytes(digest[:8], "big") >> 11
    return number / 2**53


if __name__ == "__main__":
    key = "secret"

    # Every step for ' floor' (6422) after ' the' (279), as in the blog post
    message = "279 | 6422"
    digest = hmac.digest(key.encode(), message.encode(), "sha256")
    first_8 = digest[:8]
    as_number = int.from_bytes(first_8, "big")
    kept = as_number >> 11
    print(f"1. message         {message}")
    print(f"2. HMAC-SHA256     {digest.hex()}")
    print(f"3. first 8 bytes   {first_8.hex()}")
    print(f"4. as a number     {as_number:,}")
    print(f"5. keep 53 bits    {kept:,}")
    print(f"6. divide by 2^53  {kept:,} / {2**53:,} = {kept / 2**53:.3f}")
    print()

    # Share of green tokens after each previous token
    gamma = 0.25
    n = 100_000
    fractions = []
    for prev in CHECK_PREV_TOKENS:
        green = 0
        for token in range(n):
            if keyed_uniform(key, prev, token) < gamma:
                green += 1
        fractions.append(green / n)
        print(f"after {prev:>6}: {green:,} of {n:,} green ({green / n:.2%})")

    average = sum(fractions) / len(fractions)
    print(f"range {min(fractions):.2%} to {max(fractions):.2%}, average {average:.2%}")