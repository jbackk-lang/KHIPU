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
    def __init__(self, frame_buffer_size: int = 32, classifier_fn=None):
        """`classifier_fn` (opcjonalne, 2026-08) — wstrzykiwana wtyczka
        DETECT_SCREW, przekazywana do wewnętrznego `CPUCore16`. Patrz
        `cpu.py::CPUCore16.__init__` po pełne uzasadnienie i domyślne
        zachowanie (bez podania — identyczne jak wcześniej)."""
        self.cpu = CPUCore16("CPU_CORE_16", classifier_fn=classifier_fn)
        self.lut = LUT256()
        self.timdr = TIMDRValidator()
        self.gipu = GIPUIntegrator()
        self.rope = Rope256()
        self.visual = VisualEngine()
        self.frames = FrameBuffer(maxlen=frame_buffer_size)
        self.compressor = Compressor256(self.timdr, self.gipu)

    def feed(self, word16: int):
        s = self.cpu.classify(word16)                  # (2) - respektuje wstrzyknięty classifier_fn (patrz cpu.py)
        k = self.cpu.derive_direction(s)               # (3)
        s, k = self.timdr.correct(s, k)                # (4)
        idx = self.cpu.emit_index(s, k)                # (5)
        node = self.lut.lookup(idx, s=s, k=k)           # (6)
        self.rope.append(node)                          # (7)
        self.gipu.extend_relations(self.rope.nodes)      # (8) - O(1) na slowo, patrz gipu.py
        window = self.rope.nodes[-self.frames.maxlen:]    # naprawiony bug: nie cala historia, patrz visual.py
        frame = self.visual.project(window)                # (9)
        self.frames.push(frame)
        return node

    def feed_many(self, words16):
        return [self.feed(w) for w in words16]

    def feed_stream(self, words16):
        """
        STRUMIENIOWE API (dodane 2026-08) — generator: `yield`uje każdy
        `Node256` NATYCHMIAST po przetworzeniu jednego słowa, zamiast
        budować całą listę wyników w pamięci jak `feed_many()`.

        `feed_many()` wymaga materializacji `words16` w całości I trzyma
        całą listę zwróconych węzłów w pamięci na raz — dla naprawdę
        dużego albo NIESKOŃCZONEGO źródła (generator czytający plik linia
        po linii, żywy strumień z czujnika) to nie działa/nie ma sensu.
        `feed_stream()` przyjmuje dowolny iterowalny (w tym generator) i
        zwraca węzły jeden po drugim — wywołujący przetwarza je w pętli
        `for node in system.feed_stream(words):`, bez trzymania całej
        historii wyników naraz (choć `self.rope`/`self.lut` nadal rosną
        wewnątrz, tak jak przy `feed_many()` — to NIE jest tryb
        "bezpamięciowy" względem stanu KHIPU, tylko względem LISTY WYNIKÓW
        zwracanej wywołującemu).

        Działa identycznie jak `feed_many()` co do przetwarzania (ten sam
        `feed()` na słowo, ten sam stan sznura/LUT/GIPU/TIMDR/frames) —
        różni się WYŁĄCZNIE tym, jak wyniki są dostarczane wywołującemu.
        """
        for w in words16:
            yield self.feed(w)

    def compress(self):
        return self.compressor.compress(self.rope.nodes)
