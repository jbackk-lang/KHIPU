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
        """
        Pełne przeliczenie relacji dla CAŁEJ, ustalonej listy węzłów,
        traktowanej jako sznur ZAMKNIĘTY (ostatni węzeł sąsiaduje z
        pierwszym). Właściwe dla struktur o stałym/ograniczonym rozmiarze,
        gdzie cała lista jest dostępna naraz i ma sens jako zamknięty cykl
        - np. ROPE48 (który sam siebie dokumentuje jako "brzeg domknięty"),
        albo jednorazowa analiza statycznego zrzutu sznura.

        UWAGA WYDAJNOŚCIOWA: to jest O(n) na wywołanie. Wołane raz na
        KAŻDE dodane słowo dla stale rosnącego sznura (jak dawniej robił
        `SingleCPUSystem.feed()` na `Rope256`) daje O(n²) łącznie - patrz
        `extend_relations()` niżej, które jest właściwym, wydajnym
        odpowiednikiem dla sznurów rosnących w czasie.
        """
        n = len(nodes)
        if n < 2:
            return
        for i, node in enumerate(nodes):
            neighbor = nodes[(i + 1) % n]  # sznur domknięty (izometria)
            node.r = self.relation_between(node, neighbor)

    def extend_relations(self, nodes) -> None:
        """
        NAPRAWIONY BUG WYDAJNOŚCI (patrz README.md / MODEL_PC.md "Status
        implementacji"): `SingleCPUSystem.feed()` wołał dawniej pełne
        `update_relations(self.rope.nodes)` przy KAŻDYM pojedynczym słowie,
        czyli przeliczał relacje od nowa dla całej historii sznura -
        O(n) pracy na jedno słowo, O(n²) łącznie na N słów. Zmierzone:
        4394 słów/s przy N=500, ale już tylko 793 słów/s przy N=3000 -
        wyraźna degradacja kwadratowa, nie liniowa.

        Dodatkowo poprzednie podejście miało też błąd POPRAWNOŚCI, nie
        tylko wydajności: `update_relations()` zawija sąsiedztwo modulo
        `len(nodes)`, co ma sens dla sznura o STAŁEJ długości (ROPE48),
        ale dla `Rope256` - który z definicji ROŚNIE i nigdy nie jest
        zamknięty (patrz rope.py: "długość ROPE256 nie jest ograniczona
        do stałej izometrii") - oznaczało to, że relacja węzła i-tego do
        "sąsiada" przeliczała się PONOWNIE i mogła wyjść INACZEJ za
        każdym razem, gdy sznur się wydłużał (bo punkt zawinięcia % n się
        przesuwał). Węzły "kończyły" z relacją, która nigdy nie była
        ostateczna, dopóki sznur rósł.

        `extend_relations()` jest właściwym odpowiednikiem dla sznurów
        otwartych/rosnących: liczy relację węzła WYŁĄCZNIE do jego
        bezpośredniego, ustalonego następcy w kolejności czasowej (bez
        zawijania), i po dodaniu nowego węzła aktualizuje TYLKO tę jedną,
        nową krawędź (poprzedni "ostatni" węzeł -> nowo dodany węzeł).
        To O(1) na dodane słowo, O(n) łącznie na N słów - i wynik jest
        stabilny raz obliczony, nie zmienia się przy kolejnych wywołaniach.

        Wywoływać po KAŻDYM dodaniu jednego węzła do rosnącego sznura
        (nie na całej liście od zera).
        """
        n = len(nodes)
        if n < 2:
            return
        prev, last = nodes[-2], nodes[-1]
        prev.r = self.relation_between(prev, last)
        # ostatni węzeł nie ma jeszcze następcy - zostaje domyślne R0,
        # dopóki nie dojdzie kolejny węzeł (wtedy on stanie się "prev").

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
