"""
lut256.py — LUT256 (modelPC.md, MODEL_PC_MEMORY.md, MODEL_PC_TOPLOGIC.md).

    LUT256[idx] -> NODE256

Wejście: idx = EMIT_INDEX(S,K). Wyjście: pełny stan topologiczny NODE256
(z domyślnie przypisanymi D/B/W/L/R). Modyfikowalna przez TIMDR i GIPU.
"""

from .node256 import Node256, D, B, W, L, R, derive_direction


class LUT256:
    """
    256-slotowa tablica idx -> Node256.

    DECYZJA INTERPRETACYJNA: dokumentacja nie podaje, w jaki sposób LUT256
    dobiera domyślne D/B/W/L/R dla danego idx — mówi tylko, że to LUT
    "zwraca pełny stan topologiczny" i że jest modyfikowalna przez
    TIMDR/GIPU. Domyślne wypełnienie tablicy jest tu deterministyczną
    funkcją idx (żeby dwa uruchomienia dawały ten sam wynik), a nie
    losowaniem — tak, aby cały system był powtarzalny i testowalny.
    TIMDR i GIPU mogą nadpisać dowolny wpis w trakcie działania
    (patrz timdr.py, gipu.py).
    """

    SIZE = 256

    def __init__(self):
        self._table = {}

    def _default_for(self, idx: int, s: str, k: str) -> Node256:
        d = D.ALL[idx % len(D.ALL)]
        b = B.ALL[idx % len(B.ALL)]
        w = W.ALL[idx % len(W.ALL)]
        l = L.ALL[idx % len(L.ALL)]
        r = R.ALL[idx % len(R.ALL)]
        return Node256(s=s, k=k, d=d, b=b, w=w, l=l, r=r, idx=idx)

    def lookup(self, idx: int, s: str = None, k: str = None) -> Node256:
        if not (0 <= idx <= 255):
            raise ValueError(f"idx poza zakresem [0,255]: {idx}")
        if idx not in self._table:
            if s is None or k is None:
                raise KeyError(
                    f"idx {idx} nie istnieje w LUT256 i nie podano (s,k), "
                    "żeby wygenerować wartość domyślną."
                )
            self._table[idx] = self._default_for(idx, s, k)
        return self._table[idx]

    def set(self, idx: int, node: Node256) -> None:
        """Nadpisanie wpisu — używane przez TIMDR (korekta) i GIPU (relacje)."""
        if not (0 <= idx <= 255):
            raise ValueError(f"idx poza zakresem [0,255]: {idx}")
        self._table[idx] = node

    def __len__(self):
        return len(self._table)

    def __contains__(self, idx):
        return idx in self._table
