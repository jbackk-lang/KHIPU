"""
tetragon.py — TETRAGON_4CPU: pełna architektura 4 procesorów
(MODEL_TETRAGON_4CPU.md, RESONANCE_COMM.md, README.md).

Cztery identyczne CPU_CORE_16, każdy z własnym ROPE48, dzielące jedną
LUT256, jeden TIMDR i jeden GIPU, spięte przez NODE_AXIS w figurę
rezonansową (trójkąt lub tetragon).
"""

from typing import Dict, List
from .cpu import CPUCore16
from .lut256 import LUT256
from .timdr import TIMDRValidator
from .gipu import GIPUIntegrator
from .rope48 import Rope48, LENGTH as ROPE48_LENGTH
from .axis import NodeAxis, ResonanceFigure, TETRAGON_CPUS

CPU_INPUT_STATES = 32  # README.md 5.1: "32 wejścia"


class TetragonSystem:
    def __init__(self, cpu_names=TETRAGON_CPUS):
        self.cpu_names = tuple(cpu_names)
        self.cpus = {name: CPUCore16(name) for name in self.cpu_names}
        self.ropes = {name: Rope48(name) for name in self.cpu_names}
        self.lut = LUT256()          # wspólna dla wszystkich CPU
        self.timdr = TIMDRValidator()  # globalny
        self.gipu = GIPUIntegrator()   # globalny
        self.axis = NodeAxis()
        self.figure = ResonanceFigure(
            "tetragon" if len(self.cpu_names) == 4 else "triangle",
            gipu=self.gipu,
        )
        self._last_nodes: Dict[str, object] = {}

    def feed(self, cpu_name: str, word16: int):
        """
        FLOW (MODEL_TETRAGON_4CPU.md sekcja 'FLOW'):
        1-3. CPU_X: word16 -> S_X, K_X
        4.   TIMDR waliduje (globalnie)
        5.   EMIT_INDEX -> idx_X
        6.   LUT256[idx_X] -> NODE_X
        7.   NODE_X trafia do ROPE48_X
        8.   GIPU aktualizuje relacje
        9.   NODE_AXIS spina sznury (trójkąt/tetragon)
        """
        if cpu_name not in self.cpus:
            raise ValueError(f"Nieznany CPU: {cpu_name!r}")

        cpu = self.cpus[cpu_name]
        s, k = cpu.detect_screw(word16), None
        k = cpu.derive_direction(s)
        s, k = self.timdr.correct(s, k)  # (4) walidacja/korekta globalna
        idx = cpu.emit_index(s, k)       # (5)
        node = self.lut.lookup(idx, s=s, k=k)  # (6)

        self.ropes[cpu_name].push(node)  # (7)
        self.gipu.update_relations(self.ropes[cpu_name].filled_nodes())  # (8)

        self._last_nodes[cpu_name] = node
        self.axis.update(self._last_nodes)  # (9)
        return node

    def axial_relations(self) -> Dict[str, str]:
        return self.figure.axial_relations(self._last_nodes, self.axis)

    # ------------------------------------------------------------------
    # POJEMNOŚĆ OPERACYJNA (README.md / MODEL_TETRAGON_4CPU.md sekcja 5)
    # ------------------------------------------------------------------
    def capacity_single_cpu(self) -> int:
        """32 wejścia x 48 pozycji = 1536 stanów operacyjnych."""
        return CPU_INPUT_STATES * ROPE48_LENGTH

    def capacity_total(self) -> int:
        """4 x 1536 = 6144 stanów operacyjnych."""
        return len(self.cpu_names) * self.capacity_single_cpu()

    def capacity_with_resonance(self):
        """
        Zwraca (min, max, reprezentatywna) pojemność efektywną po
        uwzględnieniu wzrostu z figury rezonansowej (+15-20% trójkąt,
        +30-40% tetragon — README.md sekcja 5.3). Wynik dla tetragonu
        mieści się w okolicach ~8000, tak jak podano w dokumentacji.
        """
        base = self.capacity_total()
        lo, hi = self.figure.resonance_boost()
        cap_min = base * (1 + lo)
        cap_max = base * (1 + hi)
        cap_mid = base * (1 + (lo + hi) / 2)
        return cap_min, cap_max, cap_mid
