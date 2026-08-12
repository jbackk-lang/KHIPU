"""
node256.py — NODE256: pełny stan topologiczny (SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md,
MODEL_PC_TOPLOGIC.md, NODE256.md).

Hierarchia (każda warstwa "wynika" z poprzedniej, zgodnie z dokumentacją):
    skręt (S) -> kierunek (K) -> droga (D) -> brzeg (B) -> szerokość (W) -> warstwa (L) -> relacje (R)

Jedyna relacja, dla której oryginalna dokumentacja podaje JAWNĄ regułę
wyprowadzenia, to S -> K (patrz SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md,
sekcja 2). D, B, W, L, R są w dokumentacji opisane jako "wynikające"
z poprzedniej warstwy, ale bez podania wzoru — w modelu przepływu danych
(MODEL_PC_TOPLOGIC.md, FLOW) to LUT256 zwraca pełny NODE256 dla danego
idx, więc D/B/W/L/R są tu traktowane jako wartości przypisywane przez
LUT256 (patrz lut256.py), a nie czyste funkcje matematyczne S/K.
"""

from dataclasses import dataclass
from typing import Optional


class S:
    """Skręt (warstwa nadrzędna) — 7 klas."""
    PLUS = "S+"      # prawoskrętny
    MINUS = "S-"     # lewoskrętny
    ZERO = "S0"      # neutralny (phi)
    UP = "S+1"       # skręt rosnący (oryg. "S↑", ASCII: S+1)
    DOWN = "S-1"     # skręt malejący (oryg. "S↓", ASCII: S-1)
    TIMES = "Sx"     # odwracalny (oryg. "S×")
    BANG = "S!"      # nieodwracalny

    ALL = (PLUS, MINUS, ZERO, UP, DOWN, TIMES, BANG)


class K:
    """Kierunek — deterministyczna funkcja skrętu."""
    RIGHT = "K>"     # oryg. "K→"
    LEFT = "K<"      # oryg. "K←"
    CW = "K)"        # oryg. "K↻" (zgodnie z ruchem wskazówek)
    CCW = "K("       # oryg. "K↺" (przeciwnie do ruchu wskazówek)
    PHI = "Kphi"     # oryg. "Kφ"

    ALL = (RIGHT, LEFT, CW, CCW, PHI)


class D:
    """Droga (przebieg po torusie/Möbiusie)."""
    STRAIGHT = "D0"
    LOOP1 = "D1"
    LOOP2 = "D2"
    MOBIUS = "DM"
    TORUS = "DT"
    LAYER_SWITCH = "DW"

    ALL = (STRAIGHT, LOOP1, LOOP2, MOBIUS, TORUS, LAYER_SWITCH)


class B:
    """Brzeg."""
    OPEN = "B0"
    CLOSED = "B1"
    MOBIUS = "BM"
    TORUS = "BT"

    ALL = (OPEN, CLOSED, MOBIUS, TORUS)


class W:
    """Szerokość."""
    CONST = "W0"
    VAR = "W+-"      # oryg. "W±"
    PHI = "Wphi"     # oryg. "Wφ"
    MOBIUS = "WM"
    TORUS = "WT"

    ALL = (CONST, VAR, PHI, MOBIUS, TORUS)


class L:
    """Warstwa."""
    ONE = "L1"
    TWO = "L2"
    MOBIUS = "LM"
    TORUS = "LT"

    ALL = (ONE, TWO, MOBIUS, TORUS)


class R:
    """Relacje."""
    PARALLEL = "R="
    CROSSING = "Rx"      # oryg. "R×"
    COUPLED = "R+"       # oryg. "R⊕"
    RESONANT = "R*"      # oryg. "R⊗"
    INDEPENDENT = "R0"

    ALL = (PARALLEL, CROSSING, COUPLED, RESONANT, INDEPENDENT)


# ---------------------------------------------------------------------
# DECYZJA INTERPRETACYJNA: SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md
# jawnie definiuje wyprowadzenie K ze S tylko dla 5 z 7 klas skrętu
# (S+, S-, S+1, S-1, S0). Dla S_TIMES ("odwracalny") i S_BANG
# ("nieodwracalny") nie podano reguły. Przyjęto:
#   - S_TIMES (odwracalny) -> K_PHI: stan odwracalny nie ma ustalonego
#     kierunku "na stałe", więc traktowany jest jak stan neutralny.
#   - S_BANG (nieodwracalny) -> K_RIGHT: nieodwracalność interpretowana
#     jako "commitment" do kierunku bazowego/domyślnego.
# Jeśli autor specyfikacji miał na myśli inne mapowanie, wystarczy
# podmienić dwa wpisy poniżej — reszta systemu jest od tego niezależna.
# ---------------------------------------------------------------------
_DERIVE_DIRECTION_TABLE = {
    S.PLUS: K.RIGHT,
    S.MINUS: K.LEFT,
    S.UP: K.CW,
    S.DOWN: K.CCW,
    S.ZERO: K.PHI,
    S.TIMES: K.PHI,   # decyzja interpretacyjna, patrz wyżej
    S.BANG: K.RIGHT,  # decyzja interpretacyjna, patrz wyżej
}


def derive_direction(s: str) -> str:
    """DERIVE_DIRECTION(S) -> K, zgodnie z SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md."""
    try:
        return _DERIVE_DIRECTION_TABLE[s]
    except KeyError:
        raise ValueError(f"Nieznana klasa skrętu: {s!r}")


@dataclass
class Node256:
    """Pełny stan topologiczny węzła (NODE256)."""
    s: str
    k: str
    d: str = D.STRAIGHT
    b: str = B.OPEN
    w: str = W.CONST
    l: str = L.ONE
    r: str = R.INDEPENDENT
    idx: Optional[int] = None

    def __post_init__(self):
        if self.s not in S.ALL:
            raise ValueError(f"Nieprawidłowy skręt: {self.s!r}")
        if self.k not in K.ALL:
            raise ValueError(f"Nieprawidłowy kierunek: {self.k!r}")
        if self.d not in D.ALL:
            raise ValueError(f"Nieprawidłowa droga: {self.d!r}")
        if self.b not in B.ALL:
            raise ValueError(f"Nieprawidłowy brzeg: {self.b!r}")
        if self.w not in W.ALL:
            raise ValueError(f"Nieprawidłowa szerokość: {self.w!r}")
        if self.l not in L.ALL:
            raise ValueError(f"Nieprawidłowa warstwa: {self.l!r}")
        if self.r not in R.ALL:
            raise ValueError(f"Nieprawidłowa relacja: {self.r!r}")

    def is_consistent(self) -> bool:
        """Sprawdza, czy K jest zgodne z regułą DERIVE_DIRECTION(S)."""
        return self.k == derive_direction(self.s)
