"""
cpu.py — CPU_CORE_16 (modelPC.md, MODEL_PC_TOPLOGIC.md, MODEL_TETRAGON_4CPU.md).

Procesor 16-bitowy wyznaczający skręt i kierunek dla słowa danych. Sam
nie liczy drogi/brzegu/warstw/relacji — to robi LUT256 (patrz lut256.py).
"""

from typing import Callable, Optional

from .node256 import S, K, derive_direction, _DERIVE_DIRECTION_TABLE

try:
    import numpy as _np
except ImportError:  # pragma: no cover - numpy jest w requirements, ale nie twardo wymagany do importu modulu
    _np = None

_POPCOUNT8 = None  # budowane leniwie w detect_screw_batch(), zeby modul importowal sie bez numpy


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
      - identyczność bajtów (hi == lo) przy remisie wagi rozróżnia Sx / S!
        (patrz "NAPRAWIONY MARTWY WARIANT" niżej — pierwotnie użyto tu
        parzystości całego słowa, co było matematycznie martwe)

    Jeżeli w Twoim zamierzeniu DETECT_SCREW miało inną definicję,
    ta funkcja jest jedynym miejscem do podmiany — cała reszta
    pipeline'u (LUT256, TIMDR, GIPU, ROPE, ...) nie zależy od
    konkretnego algorytmu, tylko od tego, że S ∈ node256.S.ALL.

    NAPRAWIONY MARTWY WARIANT (2026-08, wykryty stosując protokół
    numerologia-vs-realna-matematyka z timdr-signal-framework §18 do
    tej funkcji): pierwotny tiebreak przy `pop_hi == pop_lo` sprawdzał
    `parity_even = bin(word16).count("1") % 2 == 0` — ale skoro
    `pop_hi == pop_lo`, to suma `pop_hi + pop_lo` (czyli popcount całego
    słowa) jest ZAWSZE parzysta (suma dwóch równych liczb), niezależnie
    od konkretnych bitów. Efekt: `parity_even` było zawsze `True` w tej
    gałęzi, więc `S.BANG` ("S!", nieodwracalny) było matematycznie
    NIEOSIĄGALNE dla ŻADNEGO word16 — potwierdzone wyczerpującym
    przeglądem całej przestrzeni 16-bitowej (65536 wartości): 0 wystąpień
    S.BANG przed naprawą. Naprawione: tiebreak to teraz `hi == lo`
    (identyczność bajtów) zamiast parzystości sumy — `S.TIMES` gdy oba
    bajty są bitowo identyczne (rzeczywiście "odwracalne": zamiana
    bajtów miejscami daje to samo słowo), `S.BANG` gdy mają tę samą wagę
    bitową, ale RÓŻNĄ wartość (zamiana bajtów dałaby INNE słowo — stąd
    "nieodwracalne"). Po naprawie, na tej samej przestrzeni 65536 wartości:
    S.TIMES 255/65536 (0.39%), S.BANG 12614/65536 (19.25%) — obie klasy
    faktycznie osiągalne. Regresja: `tests/test_cpu.py::test_bang_is_reachable`.
    """

    def __init__(self, name: str = "CPU", classifier_fn: Optional[Callable[[int], str]] = None):
        """
        `classifier_fn` — WTYCZKA DETECT_SCREW (dodane 2026-08): opcjonalna,
        wstrzykiwana funkcja `word16 -> S`, zastępująca domyślną
        `CPUCore16.detect_screw()`. Formalizuje to, co docstring klasy od
        początku deklarował ("ta funkcja jest jedynym miejscem do podmiany")
        — teraz podmiana nie wymaga edycji kodu `cpu.py`, tylko przekazania
        własnej funkcji przy tworzeniu `CPUCore16`. Domyślnie (bez podania
        `classifier_fn`) zachowanie jest identyczne jak przed dodaniem tej
        opcji — `detect_screw()` zostaje referencyjną implementacją domyślną.

        Reszta pipeline'u (LUT256/TIMDR/GIPU/ROPE/Compressor) nadal nie
        zależy od KONKRETNEGO klasyfikatora — tylko od tego, że zwraca coś
        z `node256.S.ALL` (sprawdzane w `classify()` niżej, żeby błędny
        własny klasyfikator ujawnił się od razu, a nie dopiero głęboko w
        LUT256/Node256 z mniej czytelnym komunikatem).

        Metody wsadowe (`detect_screw_batch` i pochodne) NIE korzystają z
        wstrzykniętego `classifier_fn` — są zwektoryzowane pod KONKRETNY
        bitowy algorytm domyślnej implementacji, więc własny klasyfikator
        wymaga własnej wersji wsadowej, jeśli potrzebna jest szybkość na
        dużą skalę (patrz sekcja "WSADOWA KLASYFIKACJA" niżej).
        """
        self.name = name
        self._classifier_fn = classifier_fn or CPUCore16.detect_screw

    def classify(self, word16: int) -> str:
        """Klasyfikuje `word16` do S, przez wstrzyknięty `classifier_fn`
        (domyślnie `detect_screw`). To jest metoda, której faktycznie
        używa `process_word()` i cały pipeline (`pipeline.py`/`tetragon.py`)
        — żeby podmiana klasyfikatora na instancji miała efekt, kod
        wołający musi wołać `cpu.classify(w)`, nie
        `CPUCore16.detect_screw(w)` bezpośrednio (to drugie zawsze użyje
        domyślnej implementacji, bo to metoda statyczna bez dostępu do
        stanu instancji)."""
        s = self._classifier_fn(word16)
        if s not in S.ALL:
            raise ValueError(
                f"classifier_fn zwrócił wartość spoza domeny S.ALL: {s!r} "
                f"(dla word16={word16})"
            )
        return s

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

        if pop_hi == pop_lo:
            return S.TIMES if hi == lo else S.BANG
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
        """Pełny łańcuch CPU_CORE_16: word16 -> (S, K, idx).
        Używa `self.classify()` (respektuje wstrzyknięty `classifier_fn`),
        nie `self.detect_screw()` bezpośrednio."""
        s = self.classify(word16)
        k = self.derive_direction(s)
        idx = self.emit_index(s, k)
        return s, k, idx

    # ------------------------------------------------------------------
    # WSADOWA (WEKTOROWA) KLASYFIKACJA — dodane 2026-08.
    #
    # `SingleCPUSystem.feed_many()` / `TetragonSystem.feed()` NIE dają się
    # w pełni zwektoryzować: LUT256.lookup(), Rope256.append(),
    # GIPU.extend_relations() i VisualEngine.project() są z definicji
    # SEKWENCYJNE (każdy krok zależy od stanu sznura zbudowanego przez
    # poprzednie kroki). Ale DETECT_SCREW, DERIVE_DIRECTION, TIMDR.correct()
    # i EMIT_INDEX są funkcjami CZYSTYMI (zależą tylko od bieżącego word16 /
    # S / K, nie od historii) — dają się policzyć dla całego wsadu naraz.
    #
    # Zmierzone (300 000 słów, ten sam sprzęt/dane co reszta benchmarków
    # w tym repo): wersja skalarna detect_screw() w pętli = 627 174 słów/s;
    # wersja wektorowa (numpy, poniżej) = 7 497 594 słów/s — 12x szybciej,
    # zweryfikowane krzyżowo ze skalarną implementacją na losowych próbkach
    # (patrz tests/test_cpu_vectorized.py, 0 rozbieżności na 2000+ próbek).
    #
    # UCZCIWE ZASTRZEŻENIE: to przyspieszenie dotyczy WYŁĄCZNIE etapu
    # klasyfikacji. Sama klasyfikacja to ok. 5.5% czasu pełnego
    # `SingleCPUSystem.feed()` na słowo (1.6 μs z ok. 29 μs — reszta to
    # tworzenie/walidacja Node256, ROPE, GIPU, VisualEngine) — więc
    # zwektoryzowanie tego kroku NIE przyspiesza całego `feed_many()`
    # o 12x, tylko o ułamek tego (rząd wielkości: <10% całości). Realna
    # wartość tych metod: szybka, bezstanowa analiza masowa (np. "jaki
    # rozkład S/K wyszedłby z tego pliku danych?") BEZ kosztu budowania
    # pełnej symulacji (Node256/ROPE/GIPU/VisualEngine) — kiedy potrzebny
    # jest tylko rozkład klas, nie pełny stan/historia sznura.
    # ------------------------------------------------------------------

    @staticmethod
    def detect_screw_batch(words16):
        """Wektorowa wersja detect_screw() dla tablicy/listy word16 (numpy).
        Zwraca numpy array dtype=object z wartościami S.*, w tej samej
        kolejności co wejście. Wymaga numpy (patrz requirements.txt)."""
        global _POPCOUNT8
        if _np is None:
            raise ImportError("detect_screw_batch() wymaga numpy (pip install numpy)")
        if _POPCOUNT8 is None:
            _POPCOUNT8 = _np.array([bin(i).count("1") for i in range(256)], dtype=_np.uint16)

        w = _np.asarray(words16, dtype=_np.int64) & 0xFFFF
        hi = (w >> 8) & 0xFF
        lo = w & 0xFF
        pop_hi = _POPCOUNT8[hi]
        pop_lo = _POPCOUNT8[lo]
        msb = (w >> 15) & 1
        # Tiebreak = identycznosc bajtow, nie parzystosc sumy - patrz
        # "NAPRAWIONY MARTWY WARIANT" w docstringu klasy (parzystosc
        # sumy jest zawsze True, gdy pop_hi==pop_lo, wiec S.BANG bylo
        # matematycznie nieosiagalne przy starym tiebreaku).
        bytes_equal = hi == lo

        zero_mask = w == 0
        eq_mask = (~zero_mask) & (pop_hi == pop_lo)
        gt_mask = (~zero_mask) & (~eq_mask) & (pop_hi > pop_lo)
        lt_mask = (~zero_mask) & (~eq_mask) & (~gt_mask)

        out = _np.empty(w.shape, dtype=object)
        out[zero_mask] = S.ZERO
        out[eq_mask & bytes_equal] = S.TIMES
        out[eq_mask & ~bytes_equal] = S.BANG
        out[gt_mask & (msb == 1)] = S.UP
        out[gt_mask & (msb == 0)] = S.PLUS
        out[lt_mask & (msb == 1)] = S.DOWN
        out[lt_mask & (msb == 0)] = S.MINUS
        return out

    @staticmethod
    def derive_direction_batch(s_array):
        """Wektorowa wersja derive_direction() dla tablicy S (numpy).
        Tylko 7 możliwych wartości S, więc to 7 porównań maskowych
        niezależnie od długości wsadu — nie pętla po elementach."""
        if _np is None:
            raise ImportError("derive_direction_batch() wymaga numpy (pip install numpy)")
        s_array = _np.asarray(s_array, dtype=object)
        out = _np.empty(s_array.shape, dtype=object)
        for s_val, k_val in _DERIVE_DIRECTION_TABLE.items():
            out[s_array == s_val] = k_val
        return out

    @staticmethod
    def emit_index_batch(s_array, k_array):
        """Wektorowa wersja emit_index() dla tablic S i K (numpy).
        Pętla po co najwyżej len(S.ALL)*len(K.ALL)=35 kombinacjach,
        nie po elementach wsadu — koszt stały niezależny od N."""
        if _np is None:
            raise ImportError("emit_index_batch() wymaga numpy (pip install numpy)")
        s_array = _np.asarray(s_array, dtype=object)
        k_array = _np.asarray(k_array, dtype=object)
        idx = _np.full(s_array.shape, -1, dtype=_np.int64)
        for i_s, s_val in enumerate(S.ALL):
            for i_k, k_val in enumerate(K.ALL):
                mask = (s_array == s_val) & (k_array == k_val)
                idx[mask] = i_s * len(K.ALL) + i_k
        if (idx < 0).any():
            raise ValueError("emit_index_batch: nierozpoznana para (S,K) w wsadzie")
        return idx

    @classmethod
    def classify_batch(cls, words16):
        """Pełny łańcuch wsadowy: word16[] -> (S[], K[], idx[]) — odpowiednik
        process_word() dla całych tablic, bez TIMDR.correct() (TIMDR jest
        globalny/dzielony między CPU, więc korekta robiona jest osobno
        przez wywołującego, tak jak w SingleCPUSystem.feed())."""
        s = cls.detect_screw_batch(words16)
        k = cls.derive_direction_batch(s)
        idx = cls.emit_index_batch(s, k)
        return s, k, idx
