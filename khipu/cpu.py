"""
cpu.py — CPU_CORE_16 (modelPC.md, MODEL_PC_TOPLOGIC.md, MODEL_TETRAGON_4CPU.md).

Procesor 16-bitowy wyznaczający skręt i kierunek dla słowa danych. Sam
nie liczy drogi/brzegu/warstw/relacji — to robi LUT256 (patrz lut256.py).
"""

from .node256 import S, K, derive_direction


class CPUCore16:
    """
    DETECT_SCREW(word16) -> S
    DERIVE_DIRECTION(S)   -> K
    EMIT_INDEX(S, K)      -> idx

    DECYZJA INTERPRETACYJNA: żaden z dokumentów repozytorium nie podaje
    konkretnego algorytmu bitowego dla DETECT_SCREW — tylko domenę
    wyjściową S ∈ {S+, S-, S0, S+1, S-1, Sx, S!}. Poniższa implementacja
    to JEDNO z możliwych, w pełni deterministycznych mapowań word16 -> S,
    zgodne z opisem ("skręt jest nadrzędny", CPU nie liczy nic poza
    S/K/idx). Wybrano cechy bitowe, które są łatwe do zweryfikowania
    i powtarzalne:
      - word16 == 0                       -> S0 (neutralny)
      - liczba jedynek w starszym bajcie
        względem młodszego bajtu decyduje
        o "rosnący" / "malejący" / "symetryczny"
      - najstarszy bit (znak) rozróżnia warianty w ramach klasy
      - parzystość liczby jedynek rozróżnia Sx / S!  przy remisie

    Jeżeli w Twoim zamierzeniu DETECT_SCREW miało inną definicję,
    ta funkcja jest jedynym miejscem do podmiany — cała reszta
    pipeline'u (LUT256, TIMDR, GIPU, ROPE, ...) nie zależy od
    konkretnego algorytmu, tylko od tego, że S ∈ node256.S.ALL.
    """

    def __init__(self, name: str = "CPU"):
        self.name = name

    @staticmethod
    def detect_screw(word16: int) -> str:
        word16 &= 0xFFFF
        if word16 == 0:
            return S.ZERO

        hi = (word16 >> 8) & 0xFF
        lo = word16 & 0xFF
        pop_hi = bin(hi).count("1")
        pop_lo = bin(lo).count("1")
        msb = (word16 >> 15) & 1
        parity_even = bin(word16).count("1") % 2 == 0

        if pop_hi == pop_lo:
            return S.TIMES if parity_even else S.BANG
        if pop_hi > pop_lo:
            return S.UP if msb else S.PLUS
        return S.DOWN if msb else S.MINUS

    @staticmethod
    def derive_direction(s: str) -> str:
        return derive_direction(s)

    @staticmethod
    def emit_index(s: str, k: str) -> int:
        """
        EMIT_INDEX(S,K) -> idx ∈ [0..255].

        DECYZJA INTERPRETACYJNA: ponieważ K jest deterministyczną funkcją
        S (derive_direction), realnych par (S,K) jest tylko 7 — mniej niż
        256 możliwych wartości idx sugerowanych przez nazwę LUT256/NODE256.
        idx jest tu policzony jako stabilny indeks pary (S,K) w ustalonym
        porządku S.ALL x K.ALL (idx = i_s * len(K.ALL) + i_k), co mieści
        się w [0..255] i jest w pełni deterministyczne — LUT256 ma miejsce
        na dalszą rozbudowę (np. więcej klas S/K), bez zmiany interfejsu.
        """
        i_s = S.ALL.index(s)
        i_k = K.ALL.index(k)
        idx = i_s * len(K.ALL) + i_k
        if not (0 <= idx <= 255):
            raise ValueError(f"idx poza zakresem [0,255]: {idx}")
        return idx

    def process_word(self, word16: int):
        """Pełny łańcuch CPU_CORE_16: word16 -> (S, K, idx)."""
        s = self.detect_screw(word16)
        k = self.derive_direction(s)
        idx = self.emit_index(s, k)
        return s, k, idx
