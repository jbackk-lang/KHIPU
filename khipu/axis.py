"""
axis.py — NODE_AXIS + FIGURY REZONANSOWE
(MODEL_TETRAGON_4CPU.md, RESONANCE_COMM.md, README.md).

NODE_AXIS to wspólny węzeł centralny łączący sznury 3 lub 4 procesorów
(TRÓJKĄT / TETRAGON). Połączenia idą WYŁĄCZNIE przez oś — nie ma
bezpośrednich połączeń A<->B<->C<->D z pominięciem NODE_AXIS.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .node256 import Node256, S, K, R
from .gipu import GIPUIntegrator

TRIANGLE_CPUS = ("A", "B", "C")
TETRAGON_CPUS = ("A", "B", "C", "D")

TRIANGLE_EDGES = [("A", "B"), ("B", "C"), ("C", "A")]
TETRAGON_EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]
TETRAGON_DIAGONALS = [("A", "C"), ("B", "D")]


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
    """TRÓJKĄT (3 CPU) albo TETRAGON (4 CPU) — patrz README.md sekcja 3."""

    kind: str  # "triangle" | "tetragon"
    gipu: GIPUIntegrator = field(default_factory=GIPUIntegrator)

    def __post_init__(self):
        if self.kind not in ("triangle", "tetragon"):
            raise ValueError("kind musi być 'triangle' albo 'tetragon'")
        self.edges = TRIANGLE_EDGES if self.kind == "triangle" else TETRAGON_EDGES
        self.diagonals = [] if self.kind == "triangle" else TETRAGON_DIAGONALS
        self.cpus = TRIANGLE_CPUS if self.kind == "triangle" else TETRAGON_CPUS

    def axial_relations(self, nodes_by_cpu: Dict[str, Node256], axis: NodeAxis) -> Dict[str, str]:
        """R_XY_axis dla każdej krawędzi (i przekątnej w tetragonie),
        liczone jako relacja GIPU między węzłem CPU_X a stanem osi."""
        relations = {}
        for a, b in [*self.edges, *self.diagonals]:
            if a not in nodes_by_cpu or b not in nodes_by_cpu:
                continue
            relations[f"R_{a}{b}_axis"] = self.gipu.relation_between(
                nodes_by_cpu[a], nodes_by_cpu[b]
            )
        return relations

    def resonance_boost(self) -> Tuple[float, float]:
        """Zakres wzrostu pojemności wg README.md/RESONANCE_COMM.md sekcja 5.3."""
        return (0.15, 0.20) if self.kind == "triangle" else (0.30, 0.40)
