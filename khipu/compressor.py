"""
compressor.py — COMPRESSOR256 (COMPRESSOR256.md, SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md).

Logika wg dokumentacji:
    bajt -> stan topologiczny (NODE256)
    klasyfikacja po skręcie, redukcja po kierunku/drodze/brzegu/
    szerokości/warstwie/relacjach
    walidacja: TIMDR (skręt/kierunek), GIPU (sznur/węzły/odległości)
    wyjście: stan skompresowany (jeśli walidacja OK) lub stan pełny
    (jeśli walidacja odrzuci)
"""

from dataclasses import dataclass
from typing import List
from .node256 import Node256
from .timdr import TIMDRValidator
from .gipu import GIPUIntegrator


@dataclass
class CompressedRun:
    """Ciąg kolejnych węzłów identycznych na wszystkich 7 osiach, zbity w jeden."""
    node: Node256
    count: int


class Compressor256:
    """
    Kompresja przez run-length na pełnej krotce (S,K,D,B,W,L,R): kolejne
    węzły identyczne na wszystkich siedmiu osiach są zbijane w jeden wpis
    z licznikiem. Węzły, które nie przejdą walidacji TIMDR (K niespójne
    z S), są zwracane w postaci pełnej (nieskompresowanej) — zgodnie z
    opisem "stan skompresowany lub stan pełny, jeśli walidacja odrzuci".
    """

    def __init__(self, timdr: TIMDRValidator = None, gipu: GIPUIntegrator = None):
        self.timdr = timdr or TIMDRValidator()
        self.gipu = gipu or GIPUIntegrator()

    @staticmethod
    def _key(node: Node256):
        return (node.s, node.k, node.d, node.b, node.w, node.l, node.r)

    def compress(self, nodes: List[Node256]):
        """
        Zwraca listę elementów: CompressedRun (dla poprawnych, powtarzających
        się węzłów) albo Node256 "w stanie pełnym" (dla węzłów odrzuconych
        przez TIMDR — niespójne S/K).
        """
        out = []
        run_key = None
        run_node = None
        run_count = 0

        def flush():
            nonlocal run_key, run_node, run_count
            if run_node is not None:
                out.append(CompressedRun(node=run_node, count=run_count))
            run_key, run_node, run_count = None, None, 0

        for node in nodes:
            if not self.timdr.validate_pair(node.s, node.k):
                # walidacja odrzuca -> stan pełny, bez kompresji
                flush()
                out.append(node)
                continue

            key = self._key(node)
            if key == run_key:
                run_count += 1
            else:
                flush()
                run_key, run_node, run_count = key, node, 1

        flush()
        return out

    def compression_ratio(self, nodes: List[Node256]) -> float:
        """1.0 = brak kompresji, <1.0 = ile miejsca zajmuje wynik względem wejścia."""
        if not nodes:
            return 1.0
        compressed = self.compress(nodes)
        return len(compressed) / len(nodes)
