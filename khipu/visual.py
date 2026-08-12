"""
visual.py — VISUAL_ENGINE + FRAME_BUFFER (MODEL_PC_VISUAL.md, MODEL_PC_TOPLOGIC.md).

VISUAL_ENGINE tworzy obraz (FRAME) na podstawie sznura (ROPE256/ROPE48)
i LUT256. Tryby PROJECTION_2D / PROJECTION_3D są tu zaimplementowane jako
struktury danych (mapy: skręt->kolor, kierunek->wektor, itd.), a nie jako
faktyczny rendering pikseli — dokumentacja opisuje mapowania koncepcyjnie
("skręt -> kolor", "droga -> kształt"), bez konkretnej palety/geometrii,
więc renderowanie do obrazu pozostawiono jako kolejny, opcjonalny krok
(FRAME zawiera wszystkie dane potrzebne, by to zrobić w dowolnej
bibliotece graficznej).
"""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict
from .node256 import Node256

# DECYZJA INTERPRETACYJNA: konkretna paleta skręt->kolor (RGB) nie jest
# nigdzie zdefiniowana w dokumentacji ("skręt -> kolor" bez wartości) —
# przyjęto jedną, stałą, deterministyczną paletę.
_SCREW_COLOR = {
    "S+": (220, 40, 40),
    "S-": (40, 90, 220),
    "S0": (128, 128, 128),
    "S+1": (240, 160, 40),
    "S-1": (40, 160, 240),
    "Sx": (160, 40, 200),
    "S!": (20, 20, 20),
}

_DIRECTION_VECTOR = {
    "K>": (1, 0),
    "K<": (-1, 0),
    "K)": (0, 1),
    "K(": (0, -1),
    "Kphi": (0, 0),
}


@dataclass
class Frame:
    color_map: List[tuple] = field(default_factory=list)
    vector_map: List[tuple] = field(default_factory=list)
    layer_map: List[str] = field(default_factory=list)
    relation_map: List[str] = field(default_factory=list)

    def to_ascii(self) -> str:
        """Bardzo prosty podgląd tekstowy klatki (jeden znak na węzeł)."""
        symbol = {
            "S+": "+", "S-": "-", "S0": "0",
            "S+1": "^", "S-1": "v", "Sx": "x", "S!": "!",
        }
        chars = []
        for node in self._source_nodes:
            chars.append(symbol.get(node.s, "?"))
        return "".join(chars)


class VisualEngine:
    def project(self, nodes: List[Node256]) -> Frame:
        frame = Frame(
            color_map=[_SCREW_COLOR[n.s] for n in nodes],
            vector_map=[_DIRECTION_VECTOR[n.k] for n in nodes],
            layer_map=[n.l for n in nodes],
            relation_map=[n.r for n in nodes],
        )
        frame._source_nodes = list(nodes)
        return frame


class FrameBuffer:
    """Przechowuje ostatnie N klatek, umożliwia analizę zmian sznura."""

    def __init__(self, maxlen: int = 32):
        self._buffer: deque = deque(maxlen=maxlen)

    def push(self, frame: Frame) -> None:
        self._buffer.append(frame)

    def __len__(self):
        return len(self._buffer)

    def latest(self):
        return self._buffer[-1] if self._buffer else None

    def history(self) -> List[Frame]:
        return list(self._buffer)
