"""
pipeline.py — SingleCPUSystem: pełny FLOW modelu jednoprocesorowego
(modelPC.md / PRZEPŁYW_DANYCH, MODEL_PC_TOPLOGIC.md / FLOW).

    1. CPU_CORE_16 pobiera word16
    2. DETECT_SCREW -> S
    3. DERIVE_DIRECTION -> K
    4. TIMDR waliduje (S,K)
    5. EMIT_INDEX -> idx
    6. LUT256[idx] -> NODE256
    7. NODE256 trafia do ROPE256
    8. GIPU aktualizuje relacje
    9. VISUAL_ENGINE tworzy FRAME
"""

from .cpu import CPUCore16
from .lut256 import LUT256
from .timdr import TIMDRValidator
from .gipu import GIPUIntegrator
from .rope import Rope256
from .visual import VisualEngine, FrameBuffer
from .compressor import Compressor256


class SingleCPUSystem:
    def __init__(self, frame_buffer_size: int = 32):
        self.cpu = CPUCore16("CPU_CORE_16")
        self.lut = LUT256()
        self.timdr = TIMDRValidator()
        self.gipu = GIPUIntegrator()
        self.rope = Rope256()
        self.visual = VisualEngine()
        self.frames = FrameBuffer(maxlen=frame_buffer_size)
        self.compressor = Compressor256(self.timdr, self.gipu)

    def feed(self, word16: int):
        s = self.cpu.detect_screw(word16)             # (2)
        k = self.cpu.derive_direction(s)               # (3)
        s, k = self.timdr.correct(s, k)                # (4)
        idx = self.cpu.emit_index(s, k)                # (5)
        node = self.lut.lookup(idx, s=s, k=k)           # (6)
        self.rope.append(node)                          # (7)
        self.gipu.update_relations(self.rope.nodes)      # (8)
        frame = self.visual.project(self.rope.nodes)      # (9)
        self.frames.push(frame)
        return node

    def feed_many(self, words16):
        return [self.feed(w) for w in words16]

    def compress(self):
        return self.compressor.compress(self.rope.nodes)
