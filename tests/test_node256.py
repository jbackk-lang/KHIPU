from khipu.node256 import Node256, S, K, derive_direction

def test_derive_direction_documented_cases():
    assert derive_direction(S.PLUS) == K.RIGHT
    assert derive_direction(S.MINUS) == K.LEFT
    assert derive_direction(S.UP) == K.CW
    assert derive_direction(S.DOWN) == K.CCW
    assert derive_direction(S.ZERO) == K.PHI

def test_derive_direction_all_s_have_mapping():
    for s in S.ALL:
        k = derive_direction(s)
        assert k in K.ALL

def test_node256_rejects_invalid_screw():
    import pytest
    with pytest.raises(ValueError):
        Node256(s="NOPE", k=K.RIGHT)

def test_node256_is_consistent():
    n = Node256(s=S.PLUS, k=K.RIGHT)
    assert n.is_consistent()
    n2 = Node256(s=S.PLUS, k=K.LEFT)
    assert not n2.is_consistent()
