"""
Testy dla wsadowej (wektorowej) klasyfikacji CPUCore16 - patrz cpu.py
sekcja "WSADOWA (WEKTOROWA) KLASYFIKACJA". Krzyżowa weryfikacja ze
skalarną implementacją na losowych próbkach (nie tylko przykładach
ręcznych) - to dokładnie ten rodzaj testu, którego brakowało przed
naprawą błędu aliasingu LUT256 i niespójności axis.py.
"""
import random

import pytest

np = pytest.importorskip("numpy")

from khipu.cpu import CPUCore16


def test_detect_screw_batch_matches_scalar_on_random_samples():
    random.seed(1234)
    words = [random.randint(0, 0xFFFF) for _ in range(5000)] + [0, 0xFFFF, 1, 0x8000]
    expected = [CPUCore16.detect_screw(w) for w in words]
    actual = CPUCore16.detect_screw_batch(words)
    assert list(actual) == expected


def test_detect_screw_batch_matches_scalar_exhaustive_16bit_sample():
    # Cala przestrzen 16-bit (65536) - tanie obliczeniowo, wiec pelne pokrycie
    # zamiast samplowania.
    words = list(range(0x10000))
    expected = [CPUCore16.detect_screw(w) for w in words]
    actual = CPUCore16.detect_screw_batch(words)
    assert list(actual) == expected


def test_classify_batch_matches_scalar_process_word():
    random.seed(99)
    words = [random.randint(0, 0xFFFF) for _ in range(2000)]
    cpu = CPUCore16("CPU_TEST")
    expected = [cpu.process_word(w) for w in words]
    s_arr, k_arr, idx_arr = CPUCore16.classify_batch(words)
    actual = list(zip(s_arr.tolist(), k_arr.tolist(), idx_arr.tolist()))
    assert actual == expected


def test_derive_direction_batch_matches_scalar():
    from khipu.node256 import S
    s_values = list(S.ALL) * 50
    expected = [CPUCore16.derive_direction(s) for s in s_values]
    actual = CPUCore16.derive_direction_batch(s_values)
    assert list(actual) == expected


def test_emit_index_batch_matches_scalar():
    from khipu.node256 import S, K
    pairs = []
    for s in S.ALL:
        k = CPUCore16.derive_direction(s)
        pairs.append((s, k))
    s_arr = [p[0] for p in pairs]
    k_arr = [p[1] for p in pairs]
    expected = [CPUCore16.emit_index(s, k) for s, k in pairs]
    actual = CPUCore16.emit_index_batch(s_arr, k_arr)
    assert list(actual) == expected


def test_emit_index_batch_rejects_unknown_pair():
    with pytest.raises(ValueError):
        CPUCore16.emit_index_batch(["NIE_ISTNIEJE"], ["K>"])
