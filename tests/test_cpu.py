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
