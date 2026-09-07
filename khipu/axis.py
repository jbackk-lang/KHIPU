"""
axis.py — NODE_AXIS + FIGURY REZONANSOWE
(MODEL_TETRAGON_4CPU.md, RESONANCE_COMM.md, README.md).

NODE_AXIS to wspólny węzeł centralny łączący sznury 3 lub 4 procesorów
(TRÓJKĄT / TETRAGON). Połączenia idą WYŁĄCZNIE przez oś — nie ma
bezpośrednich połączeń A<->B<->C<->D z pominięciem NODE_AXIS.
"""

import itertools
import string
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .node256 import Node256, S, K, R
from .gipu import GIPUIntegrator

TRIANGLE_CPUS = ("A", "B", "C")
TETRAGON_CPUS = ("A", "B", "C", "D")

TRIANGLE_EDGES = [("A", "B"), ("B", "C"), ("C", "A")]
TETRAGON_EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]
TETRAGON_DIAGONALS = [("A", "C"), ("B", "D")]

_MAX_AUTO_CPUS = len(string.ascii_uppercase)  # 26 - etykiety A..Z


def _auto_cpu_names(n: int) -> Tuple[str, ...]:
    """Generuje N etykiet CPU (A, B, C, ...) - uzywane, gdy podano n_cpus
    zamiast jawnych cpu_names. Ograniczenie do 26 to tylko limit alfabetu
    jednoliterowego, nie architektury."""
    if not (1 <= n <= _MAX_AUTO_CPUS):
        raise ValueError(
            f"n_cpus musi byc w zakresie [1,{_MAX_AUTO_CPUS}] dla automatycznych "
            f"etykiet A-Z; dla wiekszej liczby CPU podaj wlasne cpu_names"
        )
    return tuple(string.ascii_uppercase[:n])


def _polygon_edges(cpus: Tuple[str, ...]) -> List[Tuple[str, str]]:
    """Boki wieloboku: kolejne pary w cyklu (ostatni sasiaduje z pierwszym).
    Dla n=3 daje dokladnie TRIANGLE_EDGES, dla n=4 dokladnie TETRAGON_EDGES
    (sprawdzone rownoscia) - to ta sama konstrukcja, tylko dla dowolnego N."""
    n = len(cpus)
    if n < 2:
        return []
    return [(cpus[i], cpus[(i + 1) % n]) for i in range(n)]


def _polygon_diagonals(cpus: Tuple[str, ...], edges: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Przekatne: wszystkie pozostale pary CPU, ktore nie sa bokiem.
    Dla n=3 daje [] (kazda para w trojkacie jest bokiem), dla n=4 daje
    dokladnie TETRAGON_DIAGONALS - sprawdzone rownoscia."""
    edge_set = {frozenset(e) for e in edges}
    return [pair for pair in itertools.combinations(cpus, 2) if frozenset(pair) not in edge_set]


class NodeAxis:
    """
    S_axis, K_axis, B_axis, L_axis, R_axis — stan węzła osiowego.

    DECYZJA INTERPRETACYJNA: dokumentacja nie podaje wzoru agregacji
    stanów 3-4 CPU do jednego węzła osiowego — przyjęto głosowanie
    większościowe (moda) po każdej osi osobno, co jest najprostszą
    operacją zgodną z opisem "wspólny punkt skrętu dla wszystkich CPU".
    """

    def __init__(self):
        self.s_axis = None
        self.k_axis = None
        self.b_axis = None
        self.l_axis = None
        self.r_axis = None

    @staticmethod
    def _mode(values):
        return Counter(values).most_common(1)[0][0]

    def update(self, nodes_by_cpu: Dict[str, Node256]) -> None:
        nodes = list(nodes_by_cpu.values())
        if not nodes:
            return
        self.s_axis = self._mode([n.s for n in nodes])
        self.k_axis = self._mode([n.k for n in nodes])
        self.b_axis = self._mode([n.b for n in nodes])
        self.l_axis = self._mode([n.l for n in nodes])
        self.r_axis = self._mode([n.r for n in nodes])

    def propagate_delta(self, old_s: str, new_s: str) -> bool:
        """Zwraca True, jeśli zmiana skrętu (delta_S) jest wystarczająca,
        by propagować przez oś (czyli faktycznie doszło do zmiany klasy S)."""
        return old_s != new_s


@dataclass
class ResonanceFigure:
    """TRÓJKĄT (3 CPU) albo TETRAGON (4 CPU) — patrz README.md sekcja 3.

    UOGÓLNIENIE NA DOWOLNE N CPU (2026-08): pierwotnie tylko dwie nazwane
    wartości `kind` ("triangle"/"tetragon", zaszyte na sztywno 3 i 4 CPU).
    `axial_relations()` (patrz niżej) po naprawie gwiazda-vs-graf-pełny już
    liczy relację NA CPU, nie na krawędź — więc de facto działała dla
    dowolnego N od razu. To, co faktycznie ograniczało N do 3/4, to same
    stałe `TRIANGLE_CPUS`/`TETRAGON_CPUS` zaszyte w konstruktorze. Teraz
    `kind` jest opcjonalne — można zamiast niego podać `cpu_names` (jawna
    krotka etykiet) albo `n_cpus` (liczba, etykiety A,B,C... generowane
    automatycznie). Krawędzie/przekątne dla dowolnego N liczone są ogólnym
    wzorem wieloboku (`_polygon_edges`/`_polygon_diagonals`), który dla
    N=3/4 daje DOKŁADNIE te same listy co dawne hardkodowane stałe
    (sprawdzone testem równości) — więc `kind="triangle"`/`"tetragon"`
    zachowuje się identycznie jak przed uogólnieniem, bit w bit.

    `resonance_boost()` pozostaje zdefiniowane TYLKO dla triangle/tetragon
    (0.15-0.20 / 0.30-0.40 z README.md/RESONANCE_COMM.md) — dokumentacja
    nie podaje wzoru dla innego N, więc dla figury spoza tych dwóch
    nazwanych przypadków `resonance_boost()` rzuca `NotImplementedError`
    zamiast zgadywać liczbę.
    """

    kind: Optional[str] = None  # "triangle" | "tetragon" | None (custom N przez cpu_names/n_cpus)
    cpu_names: Optional[Tuple[str, ...]] = None
    n_cpus: Optional[int] = None
    gipu: GIPUIntegrator = field(default_factory=GIPUIntegrator)

    def __post_init__(self):
        if self.kind is not None and self.kind not in ("triangle", "tetragon"):
            raise ValueError("kind musi być 'triangle', 'tetragon', albo None (z cpu_names/n_cpus)")

        if self.kind == "triangle":
            self.cpus = TRIANGLE_CPUS
        elif self.kind == "tetragon":
            self.cpus = TETRAGON_CPUS
        elif self.cpu_names is not None:
            if len(self.cpu_names) < 2:
                raise ValueError("cpu_names musi zawierać co najmniej 2 CPU")
            self.cpus = tuple(self.cpu_names)
        elif self.n_cpus is not None:
            self.cpus = _auto_cpu_names(self.n_cpus)
        else:
            raise ValueError(
                "podaj kind='triangle'/'tetragon' (nazwane presety 3/4 CPU), "
                "albo cpu_names=(...) (jawne etykiety), albo n_cpus=N (etykiety A.. generowane)"
            )

        self.edges = _polygon_edges(self.cpus)
        self.diagonals = _polygon_diagonals(self.cpus, self.edges)

    def axial_relations(self, nodes_by_cpu: Dict[str, Node256], axis: NodeAxis) -> Dict[str, str]:
        """
        NAPRAWIONA NIESPÓJNOŚĆ (2026-08): moduł jawnie dokumentuje topologię
        gwiazdy — "Połączenia idą WYŁĄCZNIE przez oś — nie ma bezpośrednich
        połączeń A<->B<->C<->D z pominięciem NODE_AXIS" (patrz docstring
        modułu wyżej). Poprzednia implementacja tej metody robiła dokładnie
        to, czego dokumentacja zabrania: liczyła `relation_between(a, b)`
        BEZPOŚREDNIO między parami CPU dla wszystkich krawędzi+przekątnych
        (czyli graf pełny K3/K4, 6 relacji dla tetragonu), a parametr `axis`
        był przyjmowany, ale nigdy nie czytany — martwy kod. 62 istniejące
        testy tego nie wyłapały, bo `test_axial_relations_covers_all_edges_and_diagonals`
        sprawdzało tylko `len(rel) == 6`, nigdy że wynik zależy od stanu osi.

        Poprawka: relacja liczona jest teraz FAKTYCZNIE przez oś — jedna
        relacja NA CPU (nie na krawędź), między węzłem tego CPU a syntetycznym
        węzłem osiowym zbudowanym z `axis.s_axis`/`axis.k_axis`. To zgodne
        z "połączenia WYŁĄCZNIE przez oś": n relacji (hub-and-spoke), nie
        n(n-1)/2 jak w grafie pełnym. Klucze mają teraz postać `R_{cpu}_axis`
        (np. `R_A_axis`), nie `R_{ab}_axis` — bo krawędź "A-B" w topologii
        gwiazdy nie istnieje jako bezpośrednie połączenie.

        DECYZJA INTERPRETACYJNA: `NodeAxis.update()` agreguje tylko s/k/b/l/r
        (nie d/w — patrz `NodeAxis.update()`), a `GIPUIntegrator.relation_between()`
        i tak czyta wyłącznie `.s`/`.k` obu węzłów, więc syntetyczny węzeł
        osiowy niesie tylko s_axis/k_axis (resztę pól wypełnia domyślnie
        `Node256`) — wystarcza to do poprawnego wyniku bez zgadywania d_axis/w_axis,
        których oś w ogóle nie utrzymuje.

        Dawne zachowanie (relacja bezpośrednia CPU<->CPU, z pominięciem osi)
        jest nadal dostępne pod jawną nazwą `direct_relations()` niżej —
        przydatne diagnostycznie do porównania "co by było, gdyby połączenia
        SZŁY bezpośrednio", ale to NIE jest to, co model dokumentuje jako
        prawdziwą architekturę.
        """
        if axis.s_axis is None or axis.k_axis is None:
            return {}
        axis_node = Node256(s=axis.s_axis, k=axis.k_axis)
        relations = {}
        for cpu in self.cpus:
            if cpu not in nodes_by_cpu:
                continue
            relations[f"R_{cpu}_axis"] = self.gipu.relation_between(
                nodes_by_cpu[cpu], axis_node
            )
        return relations

    def direct_relations(self, nodes_by_cpu: Dict[str, Node256]) -> Dict[str, str]:
        """R_XY dla każdej krawędzi (i przekątnej w tetragonie), liczone
        jako relacja GIPU BEZPOŚREDNIO między węzłami CPU_X i CPU_Y —
        z pominięciem osi. To graf pełny (K3/K4), NIE topologia gwiazdy
        udokumentowana dla tego modułu — patrz `axial_relations()` wyżej,
        które jest właściwym, zgodnym z dokumentacją odpowiednikiem.
        Zachowane jako osobna, jawnie nazwana metoda diagnostyczna (to był
        dawny, błędnie nazwany kod `axial_relations()` sprzed naprawy)."""
        relations = {}
        for a, b in [*self.edges, *self.diagonals]:
            if a not in nodes_by_cpu or b not in nodes_by_cpu:
                continue
            relations[f"R_{a}{b}"] = self.gipu.relation_between(
                nodes_by_cpu[a], nodes_by_cpu[b]
            )
        return relations

    def resonance_boost(self) -> Tuple[float, float]:
        """Zakres wzrostu pojemności wg README.md/RESONANCE_COMM.md sekcja 5.3.

        Dokumentacja klucz uje wzrost WYŁĄCZNIE po LICZBIE CPU (3 -> triangle,
        4 -> tetragon), nie po etykietach/tożsamości - więc sprawdzamy
        `len(self.cpus)`, nie `self.kind`. Dzięki temu figura zbudowana przez
        `cpu_names=(...)` z 3 albo 4 własnymi etykietami dostaje właściwy
        boost automatycznie, tak samo jak `kind="triangle"`/`"tetragon"`.
        Dla innej liczby CPU dokumentacja nie podaje wzoru, więc rzucamy
        `NotImplementedError` zamiast ekstrapolować liczbę bez podstawy
        źródłowej."""
        n = len(self.cpus)
        if n == 3:
            return (0.15, 0.20)
        if n == 4:
            return (0.30, 0.40)
        raise NotImplementedError(
            f"resonance_boost() jest zdefiniowane w dokumentacji tylko dla "
            f"3 CPU (triangle) albo 4 CPU (tetragon); ta figura ma {n} CPU - "
            f"brak podstawy źródłowej do ekstrapolacji wzrostu pojemności, "
            f"więc nie zgadujemy liczby"
        )
