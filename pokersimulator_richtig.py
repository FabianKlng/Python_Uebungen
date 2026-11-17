"""
Pokerspielsimulator
===================

Teilt zufällig fünf Karten aus, bestimmt die Pokerkombination und
wiederholt das 100 000 Mal. Am Ende werden die gezählten Anteile mit den
mathematisch korrekten Wahrscheinlichkeiten verglichen.

Quelle der Referenzwerte:
https://de.wikipedia.org/wiki/Poker#Wahrscheinlichkeiten
(2 598 960 mögliche Hände aus 52 Karten)

Benötigt Python 3.9 oder neuer.
"""

import random
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Final

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

ANZAHL_SPIELE: Final[int] = 100_000
KARTEN_PRO_HAND: Final[int] = 5
ANZAHL_MOEGLICHER_HAENDE: Final[int] = 2_598_960

# ---------------------------------------------------------------------------
# Modellierung der Karten
# ---------------------------------------------------------------------------


class Farbe(Enum):
    """Die vier Farben eines Pokerdecks."""

    KREUZ = "♣"
    PIK = "♠"
    HERZ = "♥"
    KARO = "♦"


class Symbol(Enum):
    """Die 13 Symbole (Werte). Der Zahlenwert dient zum Sortieren."""

    ZWEI = 2
    DREI = 3
    VIER = 4
    FUENF = 5
    SECHS = 6
    SIEBEN = 7
    ACHT = 8
    NEUN = 9
    ZEHN = 10
    BUBE = 11
    DAME = 12
    KOENIG = 13
    ASS = 14


@dataclass(frozen=True)
class Karte:
    """Eine Spielkarte besteht aus einer Farbe und einem Symbol."""

    farbe: Farbe
    symbol: Symbol

    def __str__(self) -> str:
        """Kurzschreibweise, z. B. 'A♠' oder '10♥'."""
        namen: dict[int, str] = {11: "B", 12: "D", 13: "K", 14: "A"}
        wert: str = namen.get(self.symbol.value, str(self.symbol.value))
        return f"{wert}{self.farbe.value}"


# Eine Hand ist eine Liste von Karten (Alias für bessere Lesbarkeit).
Hand = list[Karte]


def erstelle_deck() -> list[Karte]:
    """Erzeugt ein vollständiges Deck mit 52 Karten."""
    return [Karte(farbe, symbol) for farbe in Farbe for symbol in Symbol]


def gib_karten(deck: list[Karte], anzahl: int = KARTEN_PRO_HAND) -> Hand:
    """Zieht zufällig `anzahl` verschiedene Karten aus dem Deck.

    Das Deck selbst bleibt unverändert, daher kann es für jede Runde
    wiederverwendet werden.
    """
    return random.sample(deck, anzahl)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def zaehle_symbole(hand: Hand) -> list[int]:
    """Gibt die Häufigkeiten der Symbole absteigend sortiert zurück.

    Beispiel: Full House -> [3, 2], Zwei Paare -> [2, 2, 1]
    """
    return sorted(Counter(karte.symbol for karte in hand).values(), reverse=True)


# ---------------------------------------------------------------------------
# Funktionen für die einzelnen Kombinationen
# ---------------------------------------------------------------------------


def ist_flush(hand: Hand) -> bool:
    """Alle fünf Karten haben dieselbe Farbe."""
    return len({karte.farbe for karte in hand}) == 1


def ist_strasse(hand: Hand) -> bool:
    """Fünf aufeinanderfolgende Symbole (Ass zählt hoch oder niedrig)."""
    werte: list[int] = sorted(karte.symbol.value for karte in hand)
    # Doppelte Werte (z. B. Paare) können keine Straße sein.
    if len(set(werte)) != KARTEN_PRO_HAND:
        return False
    # Fünf verschiedene Werte, die höchstens 4 auseinanderliegen.
    if werte[-1] - werte[0] == 4:
        return True
    # Sonderfall: A-2-3-4-5 ("Wheel"), das Ass zählt hier als niedrigste Karte.
    return werte == [2, 3, 4, 5, 14]


def ist_royal_flush(hand: Hand) -> bool:
    """Straight Flush von der Zehn bis zum Ass."""
    werte: set[int] = {karte.symbol.value for karte in hand}
    return ist_flush(hand) and ist_strasse(hand) and werte == {10, 11, 12, 13, 14}


def ist_straight_flush(hand: Hand) -> bool:
    """Straße in einer Farbe (ohne Royal Flush)."""
    return ist_flush(hand) and ist_strasse(hand) and not ist_royal_flush(hand)


def ist_poker(hand: Hand) -> bool:
    """Vier Karten mit demselben Symbol (Vierling)."""
    return zaehle_symbole(hand) == [4, 1]


def ist_full_house(hand: Hand) -> bool:
    """Ein Drilling und ein Paar."""
    return zaehle_symbole(hand) == [3, 2]


def ist_drilling(hand: Hand) -> bool:
    """Drei Karten mit demselben Symbol."""
    return zaehle_symbole(hand) == [3, 1, 1]


def ist_zwei_paare(hand: Hand) -> bool:
    """Zwei verschiedene Paare."""
    return zaehle_symbole(hand) == [2, 2, 1]


def ist_paar(hand: Hand) -> bool:
    """Genau ein Paar."""
    return zaehle_symbole(hand) == [2, 1, 1, 1]


# Reihenfolge ist wichtig: von der stärksten zur schwächsten Kombination.
# Die erste zutreffende Kombination wird gewertet. Dadurch muss z. B.
# `ist_flush` nicht prüfen, ob die Hand zusätzlich eine Straße ist.
KOMBINATIONEN: Final[list[tuple[str, Callable[[Hand], bool]]]] = [
    ("Royal Flush", ist_royal_flush),
    ("Straight Flush", ist_straight_flush),
    ("Poker (Vierling)", ist_poker),
    ("Full House", ist_full_house),
    ("Flush", ist_flush),
    ("Straße", ist_strasse),
    ("Drilling", ist_drilling),
    ("Zwei Paare", ist_zwei_paare),
    ("Paar", ist_paar),
]
# "Höchste Karte" hat keine eigene Prüffunktion: Sie gilt, wenn keine der
# obigen Kombinationen zutrifft.
HOECHSTE_KARTE: Final[str] = "Höchste Karte"

# Alle Namen in Anzeigereihenfolge (stärkste zuerst).
ALLE_NAMEN: Final[list[str]] = [name for name, _ in KOMBINATIONEN] + [HOECHSTE_KARTE]

# Anzahl der möglichen Hände je Kombination (ohne Überschneidungen:
# Flush und Straße enthalten keine Straight Flushs bzw. Royal Flushs).
ANZAHL_HAENDE: Final[dict[str, int]] = {
    "Royal Flush": 4,
    "Straight Flush": 36,
    "Poker (Vierling)": 624,
    "Full House": 3_744,
    "Flush": 5_108,
    "Straße": 10_200,
    "Drilling": 54_912,
    "Zwei Paare": 123_552,
    "Paar": 1_098_240,
    "Höchste Karte": 1_302_540,
}

# Korrekte Wahrscheinlichkeiten in Prozent (Anzahl Hände / 2 598 960 * 100).
RICHTIGE_ANTEILE: Final[dict[str, float]] = {
    name: anzahl / ANZAHL_MOEGLICHER_HAENDE * 100
    for name, anzahl in ANZAHL_HAENDE.items()
}


def bewerte_hand(hand: Hand) -> str:
    """Gibt den Namen der besten Kombination einer Hand zurück."""
    for name, pruef_funktion in KOMBINATIONEN:
        if pruef_funktion(hand):
            return name
    return HOECHSTE_KARTE


# ---------------------------------------------------------------------------
# Simulation und Auswertung
# ---------------------------------------------------------------------------


def simuliere(anzahl_spiele: int) -> Counter[str]:
    """Spielt `anzahl_spiele` Hände und zählt die Kombinationen."""
    deck: list[Karte] = erstelle_deck()
    zaehler: Counter[str] = Counter()
    for _ in range(anzahl_spiele):
        hand: Hand = gib_karten(deck)
        zaehler[bewerte_hand(hand)] += 1
    return zaehler


def berechne_anteil(anzahl: int, gesamt: int) -> float:
    """Prozentualer Anteil einer Kombination an allen Spielen."""
    return anzahl / gesamt * 100


def drucke_ergebnis(zaehler: Counter[str], gesamt: int) -> None:
    """Gibt eine Tabelle mit Simulation und richtigen Werten aus."""
    # Deutsche Tausendertrennung: 100,000 -> 100.000
    print(f"\nErgebnis nach {gesamt:,} Spielen\n".replace(",", "."))
    kopf: str = (
        f"{'Kombination':<18}{'Anzahl':>9}"
        f"{'Simuliert %':>14}{'Richtig %':>12}{'Differenz':>12}"
    )
    print(kopf)
    print("-" * len(kopf))

    for name in ALLE_NAMEN:
        anzahl: int = zaehler[name]
        simuliert: float = berechne_anteil(anzahl, gesamt)
        richtig: float = RICHTIGE_ANTEILE[name]
        print(
            f"{name:<18}{anzahl:>9}{simuliert:>13.4f}%"
            f"{richtig:>11.4f}%{simuliert - richtig:>+12.4f}"
        )


def main() -> None:
    """Zeigt eine Beispielhand und führt danach die Simulation aus."""
    beispiel_hand: Hand = gib_karten(erstelle_deck())
    print("Beispielhand:", " ".join(str(karte) for karte in beispiel_hand))
    print("Kombination: ", bewerte_hand(beispiel_hand))

    ergebnis: Counter[str] = simuliere(ANZAHL_SPIELE)
    drucke_ergebnis(ergebnis, ANZAHL_SPIELE)


if __name__ == "__main__":
    main()
