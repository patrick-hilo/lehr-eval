_ANIMALS = (
    "adler",
    "amsel",
    "baer",
    "biber",
    "dachs",
    "delfin",
    "eichhoernchen",
    "elch",
    "ente",
    "falke",
    "fink",
    "fisch",
    "fuchs",
    "gans",
    "hamster",
    "hase",
    "hirsch",
    "hund",
    "igel",
    "katze",
    "kranich",
    "lachs",
    "lama",
    "loewe",
    "luchs",
    "maus",
    "milan",
    "otter",
    "panda",
    "pferd",
    "reh",
    "robbe",
    "schaf",
    "schwan",
    "specht",
    "storch",
    "tiger",
    "wal",
    "wolf",
    "ziege",
)

_ADJECTIVES = (
    "blauer",
    "gruener",
    "kleiner",
    "grosser",
    "schneller",
    "leiser",
    "bunter",
    "heller",
    "ruhiger",
    "starker",
    "wacher",
    "klarer",
    "froher",
    "flinker",
    "sanfter",
    "mutiger",
    "freier",
    "frischer",
    "warmer",
    "sicherer",
)


def code_for_index(index: int) -> str:
    if index < 0:
        raise ValueError("negative index is not allowed")

    if index < len(_ANIMALS):
        return _ANIMALS[index]

    compound_index = index - len(_ANIMALS)
    adjective = _ADJECTIVES[compound_index // len(_ANIMALS) % len(_ADJECTIVES)]
    animal = _ANIMALS[compound_index % len(_ANIMALS)]
    cycle = compound_index // (len(_ANIMALS) * len(_ADJECTIVES))

    if cycle:
        adjective = f"{adjective}{cycle + 1}"

    return f"{adjective} {animal}"
