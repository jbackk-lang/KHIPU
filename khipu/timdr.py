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
    udział nie odbiegał od 1/2 bardziej niż o dopuszczalną tolerancję.

    NAPRAWIONA TOLERANCJA MARTWA (2026-08, wykryte stosując protokół
    numerologia-vs-realna-matematyka z timdr-signal-framework §18 do tej
    reguły): pierwotna tolerancja `φ - 1 ≈ 0.618` jest WIĘKSZA niż
    matematycznie możliwe maksymalne odchylenie `|balance - 0.5|`, które
    wynosi co najwyżej `0.5` (bo `balance = udział ∈ [0,1]`, więc skrajne
    wartości 0 i 1 dają odchylenie dokładnie 0.5, nigdy więcej). Skutek:
    `|balance - 0.5| <= 0.5 < φ - 1` ZAWSZE, dla KAŻDEGO możliwego sznura
    — `validate_rope()` z domyślną tolerancją była matematycznie
    NIEZDOLNA do zwrócenia `False`, niezależnie od danych (potwierdzone:
    nawet sznur złożony w 100% z jednego kierunku, `balance=1.0`,
    odchylenie `0.5`, wciąż mieści się w tolerancji `0.618`). Dodatkowo
    `validate_rope()`/`rope_balance()` nie są wołane przez żaden inny
    moduł w działającym pipeline (`pipeline.py`, `tetragon.py`) — więc
    ta "walidacja globalna" była podwójnie martwa: nieużywana i, gdyby
    użyta, bezwarunkowo zawsze prawdziwa. Naprawione: tolerancja to teraz
    `2 - φ = 1/φ² ≈ 0.382` — również liczba wprost wyprowadzona z φ
    (tożsamość `φ² = φ + 1` ⟹ `1/φ² = 2 - φ`), ale MNIEJSZA od 0.5, więc
    reguła może faktycznie odrzucić skrajnie niezbalansowany sznur
    (odrzuca, gdy udział "rosnących" < 11.8% lub > 88.2%). Zweryfikowane:
    200 000 losowych realnych słów przez pełny pipeline daje
    `balance≈0.501` (przechodzi, jak powinno dla losowych/zbalansowanych
    danych), sztucznie skrajny sznur (100% jeden kierunek) teraz
    poprawnie NIE przechodzi z domyślną tolerancją. Regresja:
    `tests/test_timdr.py::test_default_tolerance_can_actually_reject_extreme_rope`.
    """

    def __init__(self, tolerance: float = 2 - PHI):
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
