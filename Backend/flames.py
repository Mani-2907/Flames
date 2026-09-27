RELATIONSHIPS = {
    "F": (
        "Friends",
        "A friendly connection built on good company and shared laughs.",
    ),
    "L": (
        "Love",
        "A sweet spark and a little romance are in this playful result.",
    ),
    "A": (
        "Affection",
        "A caring bond with warmth, kindness, and plenty of affection.",
    ),
    "M": (
        "Marriage",
        "The game imagines a lasting partnership full of teamwork.",
    ),
    "E": (
        "Enemies",
        "Different personalities can make for a lively, unpredictable duo.",
    ),
    "S": (
        "Siblings",
        "A close, comfortable bond with the fun of family-like teasing.",
    ),
}


def calculate_flames(name1: str, name2: str) -> str:
    """Return the FLAMES category code for two names."""
    first_letters = [char for char in name1.casefold() if char.isalpha()]
    second_letters = [char for char in name2.casefold() if char.isalpha()]

    for char in first_letters.copy():
        if char in second_letters:
            first_letters.remove(char)
            second_letters.remove(char)

    remaining_count = len(first_letters) + len(second_letters)
    flames = list("FLAMES")

    if remaining_count == 0:
        return "F"

    index = 0
    while len(flames) > 1:
        index = (index + remaining_count - 1) % len(flames)
        flames.pop(index)

    return flames[0]