"""
gipu.py — GIPU: globalny integrator sznurów
(modelPC.md / VALIDATION_LAYER, MODEL_PC_TOPLOGIC.md, MODEL_TETRAGON_4CPU.md).

Rola wg dokumentacji:
    - zarządzanie sznurem/sznurami (ROPE256 / ROPE48_A..D)
    - walidacja węzłów, odległości, przejść warstw
    - aktualizacja relacji (R) i tablicy LUT256
    - utrzymywanie figur rezonansowych (trójkąt/tetragon) — patrz axis.py
"""

from .node256 import R


class GIPUIntegrator:
    """
    DECYZJA INTERPRETACYJNA: reguła przypisania relacji R między dwoma
    sąsiednimi węzłami nie jest w dokumentacji podana wprost — tylko
    domena R ∈ {R=, R×, R⊕, R⊗, R0}. Przyjęto najprostszą, symetryczną
    regułę zgodną z nazwami relacji:
        - taki sam skręt i kierunek       -> R⊗ (rezonans)
        - taki sam skręt, inny kierunek   -> R⊕ (sprzężenie)
        - inny skręt, ten sam kierunek    -> R=  (równoległe)
        - oba różne                       -> R×  (przecinające)
        - jeden z węzłów neutralny (S0)   -> R0  (niezależne)
    """

    def relation_between(self, a, b) -> str:
        if a.s == "S0" or b.s == "S0":
            return R.INDEPENDENT
        same_s = a.s == b.s
        same_k = a.k == b.k
        if same_s and same_k:
            return R.RESONANT
        if same_s and not same_k:
            return R.COUPLED
        if not same_s and same_k:
            return R.PARALLEL
        return R.CROSSING

    def update_relations(self, nodes) -> None:
        """Aktualizuje pole `r` każdego węzła na podstawie sąsiada w sznurze."""
        n = len(nodes)
        if n < 2:
            return
        for i, node in enumerate(nodes):
            neighbor = nodes[(i + 1) % n]  # sznur domknięty (izometria)
            node.r = self.relation_between(node, neighbor)

    def update_lut(self, lut, nodes) -> None:
        """Zapisuje bieżące węzły z powrotem do LUT256 pod ich idx."""
        for node in nodes:
            if node.idx is not None:
                lut.set(node.idx, node)

    def distances(self, nodes):
        """Odległości (w pozycjach) między kolejnymi węzłami o tym samym S."""
        result = []
        positions_by_s = {}
        for i, node in enumerate(nodes):
            if node.s in positions_by_s:
                result.append(i - positions_by_s[node.s])
            positions_by_s[node.s] = i
        return result
