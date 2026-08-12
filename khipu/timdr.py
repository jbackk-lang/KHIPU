"""
timdr.py — TIMDR: globalny walidator skrętu/kierunku
(modelPC.md / VALIDATION_LAYER, MODEL_PC_TOPLOGIC.md, MODEL_TETRAGON_4CPU.md).

Rola wg dokumentacji:
    - walidacja skrętu S
    - walidacja kierunku K
    - pilnowanie "osi 1/2 i φ"
    - może wymusić korektę S/K (globalnie, dla wielu CPU naraz)
"""

from .node256 import S, derive_direction

PHI = (1 + 5 ** 0.5) / 2  # złoty podział, ok. 1.618


class TIMDRValidator:
    """
    DECYZJA INTERPRETACYJNA: "zasada 1/2 i φ" nie ma w dokumentacji
    podanego wzoru. Zaimplementowano ją jako kontrolę równowagi sznura:
    licząc udział węzłów "rosnących" (S+, S+1) wśród wszystkich węzłów
    o zdefiniowanym trendzie (S+, S-, S+1, S-1) i pilnując, żeby ten
    udział nie odbiegał od 1/2 bardziej niż o (φ - 1) ≈ 0.618 - 0.5.
    To najbliższa liczbowa interpretacja frazy "zasada 1/2 i φ", jaką
    dawało się wyprowadzić z tekstu specyfikacji bez dodatkowych założeń.
    """

    def __init__(self, tolerance: float = PHI - 1):
        self.tolerance = tolerance

    def validate_pair(self, s: str, k: str) -> bool:
        """Sprawdza, czy K jest zgodne z regułą DERIVE_DIRECTION(S)."""
        return k == derive_direction(s)

    def correct(self, s: str, k: str):
        """
        Jeśli para (S,K) jest niespójna, TIMDR "wymusza korektę" —
        nadpisuje K zgodnie z regułą wyprowadzenia dla danego S.
        """
        if self.validate_pair(s, k):
            return s, k
        return s, derive_direction(s)

    def rope_balance(self, nodes) -> float:
        """Udział węzłów 'rosnących' (S+, S+1) wśród S+/S-/S+1/S-1."""
        trend = [n.s for n in nodes if n.s in (S.PLUS, S.MINUS, S.UP, S.DOWN)]
        if not trend:
            return 0.5
        up = sum(1 for s in trend if s in (S.PLUS, S.UP))
        return up / len(trend)

    def validate_rope(self, nodes) -> bool:
        """Zasada 1/2 i φ: udział 'rosnących' musi mieścić się w [0.5-tol, 0.5+tol]."""
        balance = self.rope_balance(nodes)
        return abs(balance - 0.5) <= self.tolerance
