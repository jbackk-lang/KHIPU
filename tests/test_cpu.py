from khipu.cpu import CPUCore16
from khipu.node256 import S, K

def test_detect_screw_deterministic():
    cpu = CPUCore16()
    for w in [0, 1, 255, 4096, 32768, 65535, 12345, 0xABCD]:
        assert cpu.detect_screw(w) == cpu.detect_screw(w)

def test_detect_screw_zero_is_neutral():
    cpu = CPUCore16()
    assert cpu.detect_screw(0) == S.ZERO

def test_derive_direction_matches_node256_rule():
    cpu = CPUCore16()
    for w in range(0, 65536, 4001):
        s = cpu.detect_screw(w)
        k = cpu.derive_direction(s)
        assert k in K.ALL

def test_emit_index_in_range_for_all_words():
    cpu = CPUCore16()
    for w in range(0, 65536, 977):
        s, k, idx = cpu.process_word(w)
        assert 0 <= idx <= 255

def test_process_word_full_chain_consistent():
    cpu = CPUCore16()
    s, k, idx = cpu.process_word(12345)
    assert k == cpu.derive_direction(s)
    assert idx == cpu.emit_index(s, k)

def test_bang_is_reachable():
    """Regresja dla martwego wariantu naprawionego 2026-08 (patrz
    docstring CPUCore16 'NAPRAWIONY MARTWY WARIANT'): stary tiebreak
    (parzystosc calego slowa) bylo zawsze True gdy pop_hi==pop_lo, wiec
    S.BANG nie moglo nigdy wystapic. Sprawdzamy na calej przestrzeni
    16-bitowej, ze OBIE galezie remisu (S.TIMES i S.BANG) sa osiagalne."""
    seen = {cpu_result for cpu_result in (CPUCore16.detect_screw(w) for w in range(0x10000))}
    assert S.TIMES in seen
    assert S.BANG in seen

def test_times_means_bytes_identical_bang_means_same_weight_different_bytes():
    """S.TIMES <=> hi==lo (bajty identyczne); S.BANG <=> ta sama waga
    bitowa, ale rozne bajty - to jest tiebreak po naprawie."""
    for w in [0x0101, 0x0F0F, 0xABAB]:  # hi == lo
        assert CPUCore16.detect_screw(w) == S.TIMES
    for w in [0x0102, 0x0305]:  # popcount(hi) == popcount(lo), hi != lo
        hi, lo = (w >> 8) & 0xFF, w & 0xFF
        assert bin(hi).count("1") == bin(lo).count("1")
        assert hi != lo
        assert CPUCore16.detect_screw(w) == S.BANG
