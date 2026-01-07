ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode_base62(num: int) -> str:
    if num < 0:
        raise ValueError("Number must be non-negative")

    if num == 0:
        return ALPHABET[0]

    chars = []
    while num > 0:
        num, remainder = divmod(num, BASE)
        chars.append(ALPHABET[remainder])

    return "".join(reversed(chars))
