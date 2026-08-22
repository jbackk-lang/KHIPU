"""
benchmarks/parallel_vs_sequential.py

Eksperyment: czy realne zrownoleglenie (multiprocessing, prawdziwe procesy
systemowe) 4 "rdzeni" TIMDR-CPU daje realne przyspieszenie wzgledem
sekwencyjnego przetwarzania w jednym procesie/watku.

Watki NIE sa uzyte celowo: dla pracy CPU-bound w czystym Pythonie GIL
i tak serializuje wykonanie, wiec jedyny sposob na prawdziwa rownoleglosc
to osobne procesy systemowe (`multiprocessing`).

Projekt eksperymentu: kazdy z N "CPU" dostaje SWOJA niezalezna 1/N
strumienia slow i przetwarza ja WLASNYM, w pelni lokalnym pipeline'em
(CPUCore16 + LUT256 + TIMDR + Rope48 + GIPU.update_relations) - bez
globalnego stanu dzielonego miedzy procesami (dzielenie zywych obiektow
Pythona miedzy procesami jest kosztowne/skomplikowane przez pickle, wiec
eksperyment celowo pomija synchronizacje NODE_AXIS w czasie rzeczywistym
miedzy procesami - mierzy WYLACZNIE surowa przepustowosc przetwarzania
slow, bo o to bylo pytanie, nie o pelna wiernosc modelowi TetragonSystem).

===========================================================================
ZMIERZONE WYNIKI (2026-08-22, sandbox z `os.cpu_count() == 2`, WAZNE
zastrzezenie: NIE prawdziwy 4+ rdzeniowy Ryzen - patrz interpretacja nizej):
===========================================================================

    200 000 slow, 4 rownolegle strumienie (oversubskrybcja 4 procesy / 2 rdzenie):
        sekwencyjnie (1 proces): 27 432 slow/s
        rownolegle (Pool(4)):    36 513 slow/s
        przyspieszenie: 1.33x     (fizyczny sufit na 2 rdzeniach: 2.00x)
        efektywnosc wzgledem fizycznego sufitu: ~66%

    200 000 slow, 2 rownolegle strumienie (dopasowane do realnej liczby rdzeni):
        sekwencyjnie (1 proces): 26 190 slow/s
        rownolegle (Pool(2)):    36 413 slow/s
        przyspieszenie: 1.39x     (teoretyczny sufit na 2 rdzeniach: 2.00x)
        efektywnosc wzgledem sufitu: ~70%

Sanity check: wyniki (total_pushed per CPU) IDENTYCZNE w obu trybach -
rownoleglenie nie zmienia poprawnosci, tylko czas.

INTERPRETACJA (uczciwie, nie ekstrapolujac na sile):
- Rownoleglosc REALNIE pomaga (36-37 tys. > 26-27 tys. slow/s), ale
  skromnie - nie liniowo z liczba "CPU", bo (a) sandbox ma fizycznie
  tylko 2 rdzenie, wiec test na "4 CPU" jest oversubskrybowany i nie moze
  w ogole osiagnac 4x, (b) narzut multiprocessingu (spawn procesu, pickle
  danych miedzy procesami) zjada czesc zysku przy tak lekkiej pracy na
  pojedyncze slowo.
- Na prawdziwym 4+ rdzeniowym Ryzenie NALEZY spodziewac sie wiekszego
  przyspieszenia niz tutaj (bo nie bedzie oversubskrypcji), ale
  prawdopodobnie wciaz ponizej pelnych 4.00x - efektywnosc rzedu 65-75%
  zmierzona tutaj na 2 rdzeniach jest typowa dla multiprocessingu przy
  lekkich zadaniach i nie ma powodu zakladac, ze na wiekszej liczbie
  rdzeni bedzie to istotnie lepsze bez zmiany podejscia (np. wiekszych
  paczek pracy na proces, co juz tu jest zrobione - kazdy proces dostaje
  cala 1/N calosci naraz, nie male porcje w petli).
- To NIE jest zmierzone na docelowym sprzecie uzytkownika - jesli masz
  dostep do maszyny z 4+ rdzeniami, uruchom `python3 benchmarks/parallel_vs_sequential.py`
  tam, zeby dostac liczby faktycznie odpowiadajace pytaniu "co da 4 CPU
  na prawdziwym Ryzenie".
"""
import os
import sys
import time
import random
import multiprocessing as mp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from khipu.cpu import CPUCore16
from khipu.lut256 import LUT256
from khipu.timdr import TIMDRValidator
from khipu.gipu import GIPUIntegrator
from khipu.rope48 import Rope48


def process_chunk(args):
    """Przetwarza jeden fragment slow WLASNYM, lokalnym pipeline'em - jak
    jeden 'CPU' z TetragonSystem, ale calkowicie niezalezny (wlasny
    LUT/TIMDR/GIPU/rope, zeby dalo sie to bezpiecznie odpalic w osobnym
    procesie bez dzielenia zywych obiektow)."""
    name, words = args
    cpu = CPUCore16(name)
    lut = LUT256()
    timdr = TIMDRValidator()
    gipu = GIPUIntegrator()
    rope = Rope48(name)

    for w in words:
        s = cpu.detect_screw(w)
        k = cpu.derive_direction(s)
        s, k = timdr.correct(s, k)
        idx = cpu.emit_index(s, k)
        node = lut.lookup(idx, s=s, k=k)
        rope.push(node)
        gipu.update_relations(rope.filled_nodes())  # O(48) stale, bezpieczne przy Rope48

    return name, len(words), rope.total_pushed


def run_comparison(total_words: int, n_streams: int, seed: int = 2026):
    """Porownuje sekwencyjne i rownolegle przetworzenie `total_words` slow
    podzielonych na `n_streams` niezaleznych strumieni. Zwraca dict z
    surowymi czasami i przyspieszeniem."""
    random.seed(seed)
    names = [chr(ord("A") + i) for i in range(n_streams)]
    chunk_size = total_words // n_streams
    chunks = [
        (name, [random.randint(0, 0xFFFF) for _ in range(chunk_size)])
        for name in names
    ]

    t0 = time.perf_counter()
    seq_results = [process_chunk(c) for c in chunks]
    seq_dt = time.perf_counter() - t0

    t0 = time.perf_counter()
    with mp.Pool(processes=n_streams) as pool:
        par_results = pool.map(process_chunk, chunks)
    par_dt = time.perf_counter() - t0

    assert sorted(seq_results) == sorted(par_results), "WYNIKI SIE NIE ZGADZAJA miedzy trybami!"

    return {
        "n_streams": n_streams,
        "total_words": total_words,
        "seq_dt": seq_dt,
        "par_dt": par_dt,
        "seq_rate": total_words / seq_dt,
        "par_rate": total_words / par_dt,
        "speedup": seq_dt / par_dt,
        "cpu_count": os.cpu_count(),
    }


def _print_result(r):
    print(f"  sekwencyjnie: {r['seq_rate']:,.0f} slow/s")
    print(f"  rownolegle ({r['n_streams']} procesy): {r['par_rate']:,.0f} slow/s")
    print(f"  przyspieszenie: {r['speedup']:.2f}x "
          f"(fizyczny sufit na {r['cpu_count']} rdzeniach: {min(r['n_streams'], r['cpu_count']):.2f}x)")
    print()


def main():
    print(f"os.cpu_count() = {os.cpu_count()} "
          f"(UWAGA: jesli to < 4, test na 4 strumienie jest oversubskrybowany)")
    print()

    print("=== 4 rownolegle strumienie ===")
    r4 = run_comparison(total_words=200_000, n_streams=4)
    _print_result(r4)

    print("=== 2 rownolegle strumienie (dopasowane do liczby rdzeni w tym sandboxie) ===")
    r2 = run_comparison(total_words=200_000, n_streams=2)
    _print_result(r2)

    print("Sanity check: wyniki identyczne sekwencyjnie/rownolegle w obu testach - OK")


if __name__ == "__main__":
    main()
