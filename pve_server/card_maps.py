"""Card mapping constants for converting between internal and display representations."""

EnvCard2RealCard = {
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
    17: "2",
    20: "X",
    30: "D",
}

RealCard2EnvCard = {v: k for k, v in EnvCard2RealCard.items()}

Card2Suit = {
    "3": ["S3", "H3", "D3", "C3"],
    "4": ["S4", "H4", "D4", "C4"],
    "5": ["S5", "H5", "D5", "C5"],
    "6": ["S6", "H6", "D6", "C6"],
    "7": ["S7", "H7", "D7", "C7"],
    "8": ["S8", "H8", "D8", "C8"],
    "9": ["S9", "H9", "D9", "C9"],
    "T": ["ST", "HT", "DT", "CT"],
    "J": ["SJ", "HJ", "DJ", "CJ"],
    "Q": ["SQ", "HQ", "DQ", "CQ"],
    "K": ["SK", "HK", "DK", "CK"],
    "A": ["SA", "HA", "DA", "CA"],
    "2": ["S2", "H2", "D2", "C2"],
    "X": ["BJ"],
    "D": ["RJ"],
}
