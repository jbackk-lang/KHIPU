from khipu.compressor import Compressor256, CompressedRun
from khipu.node256 import Node256, S, K
from khipu.timdr import TIMDRValidator

def test_compresses_repeated_identical_nodes():
    c = Compressor256()
    n = Node256(s=S.PLUS, k=K.RIGHT)
    result = c.compress([n, n, n])
    assert len(result) == 1
    assert isinstance(result[0], CompressedRun)
    assert result[0].count == 3

def test_different_nodes_not_merged():
    c = Compressor256()
    a = Node256(s=S.PLUS, k=K.RIGHT)
    b = Node256(s=S.MINUS, k=K.LEFT)
    result = c.compress([a, b])
    assert len(result) == 2

def test_invalid_node_kept_as_full_state():
    c = Compressor256()
    bad = Node256(s=S.PLUS, k=K.LEFT)  # niespójne S/K -> TIMDR odrzuca
    result = c.compress([bad])
    assert result == [bad]  # zwrócony wprost, nie jako CompressedRun

def test_compression_ratio_bounds():
    c = Compressor256()
    n = Node256(s=S.PLUS, k=K.RIGHT)
    assert c.compression_ratio([]) == 1.0
    assert c.compression_ratio([n, n, n, n]) == 0.25
