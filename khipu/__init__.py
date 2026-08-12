"""
khipu — implementacja modeli opisanych w dokumentacji repozytorium
(MODEL_PC.md, MODEL_TETRAGON_4CPU.md).

UWAGA: część oryginalnej dokumentacji (README, MODEL_TETRAGON_4CPU,
RESONANCE_COMM, modelPC, MODEL_PC_TOPLOGIC, ...) opisuje architekturę
na poziomie koncepcyjnym/prozy, bez podania konkretnych algorytmów
bitowych. W kilku miejscach ten pakiet musiał dokonać interpretacyjnych
wyborów, żeby specyfikacja stała się uruchamialnym kodem. Każdy taki
wybór jest oznaczony komentarzem "DECYZJA INTERPRETACYJNA" w miejscu,
gdzie występuje, i podsumowany w MODEL_PC.md / MODEL_TETRAGON_4CPU.md
w sekcji "Status implementacji".
"""

from .node256 import Node256, S, K, D, B, W, L, R, derive_direction
from .cpu import CPUCore16
from .lut256 import LUT256
from .timdr import TIMDRValidator
from .gipu import GIPUIntegrator
from .rope import Rope256
from .rope48 import Rope48
from .compressor import Compressor256
from .visual import VisualEngine, Frame, FrameBuffer
from .axis import NodeAxis, ResonanceFigure
from .tetragon import TetragonSystem
from .pipeline import SingleCPUSystem

__all__ = [
    "Node256", "S", "K", "D", "B", "W", "L", "R", "derive_direction",
    "CPUCore16", "LUT256", "TIMDRValidator", "GIPUIntegrator",
    "Rope256", "Rope48", "Compressor256",
    "VisualEngine", "Frame", "FrameBuffer",
    "NodeAxis", "ResonanceFigure", "TetragonSystem", "SingleCPUSystem",
]
