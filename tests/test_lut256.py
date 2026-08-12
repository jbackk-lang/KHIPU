import pytest
from khipu.lut256 import LUT256
from khipu.node256 import S, K, Node256

def test_lookup_generates_default_when_missing():
    lut = LUT256()
    node = lut.lookup(5, s=S.PLUS, k=K.RIGHT)
    assert node.idx == 5
    assert node.s == S.PLUS

def test_lookup_without_sk_raises_if_absent():
    lut = LUT256()
    with pytest.raises(KeyError):
        lut.lookup(3)

def test_lookup_is_deterministic_across_instances():
    a, b = LUT256(), LUT256()
    na = a.lookup(10, s=S.MINUS, k=K.LEFT)
    nb = b.lookup(10, s=S.MINUS, k=K.LEFT)
    assert (na.d, na.b, na.w, na.l, na.r) == (nb.d, nb.b, nb.w, nb.l, nb.r)

def test_set_overwrites_entry():
    lut = LUT256()
    lut.lookup(1, s=S.PLUS, k=K.RIGHT)
    override = Node256(s=S.MINUS, k=K.LEFT, idx=1)
    lut.set(1, override)
    assert lut.lookup(1).s == S.MINUS

def test_idx_out_of_range_rejected():
    lut = LUT256()
    with pytest.raises(ValueError):
        lut.lookup(300, s=S.PLUS, k=K.RIGHT)
