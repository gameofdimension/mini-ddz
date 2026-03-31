"""Deck initialization, card dealing, and suit format conversion utilities."""

import random

from card_maps import Card2Suit, EnvCard2RealCard, RealCard2EnvCard


def _init_deck():
    """Initialize a standard Dou Dizhu deck."""
    deck = []
    for rank in ["3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A", "2"]:
        for _suit in ["S", "H", "D", "C"]:
            deck.append(RealCard2EnvCard[rank])
    deck.append(20)  # Black Joker (X)
    deck.append(30)  # Red Joker (D)
    return deck


def _deal_cards():
    """Deal cards for a game."""
    deck = _init_deck()
    random.shuffle(deck)

    landlord_cards = sorted(deck[:20], reverse=True)
    landlord_down_cards = sorted(deck[20:37], reverse=True)
    landlord_up_cards = sorted(deck[37:54], reverse=True)
    three_landlord_cards = sorted(deck[:3], reverse=True)

    return {
        0: landlord_cards,
        1: landlord_down_cards,
        2: landlord_up_cards,
        "three_landlord_cards": three_landlord_cards,
    }


def _cards_to_suit_format(cards):
    """Convert env cards to suit format for replay."""
    result = []
    card_counts = {}
    for card in cards:
        card_char = EnvCard2RealCard[card]
        idx = card_counts.get(card_char, 0)
        result.append(Card2Suit[card_char][idx])
        card_counts[card_char] = idx + 1
    return result


def _assign_card_suits(cards):
    """Assign suit to each card based on its position among cards of the same rank.

    Returns a list of (card_value, suit) tuples.
    """
    result = []
    card_counts = {}
    for card in cards:
        card_char = EnvCard2RealCard[card]
        idx = card_counts.get(card_char, 0)
        suit = Card2Suit[card_char][idx]
        result.append((card, suit))
        card_counts[card_char] = idx + 1
    return result


def _action_to_suit_format(action, player_hand_with_suits):
    """Convert action to suit format using pre-assigned suits.

    Args:
        action: List of card values (e.g., [3, 3] for a pair of 3s)
        player_hand_with_suits: List of (card_value, suit) tuples

    Returns:
        Space-separated string of card suits (e.g., 'S3 H3')
    """
    if action == [] or action == "pass":
        return "pass"

    result = []
    temp_hand = player_hand_with_suits.copy()
    for card in action:
        for i, (hand_card, suit) in enumerate(temp_hand):
            if hand_card == card:
                result.append(suit)
                temp_hand.pop(i)
                break
    return " ".join(result)
