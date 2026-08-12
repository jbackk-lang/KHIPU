import pytest
from khipu.rope48 import Rope48, LENGTH
from khipu.node256 import Node256, S, K

def test_isometry_fixed_length():
    rope = Rope48("A")
    assert len(rope) == LENGTH == 48
    assert rope.is_isometric()

def test_set_get_roundtrip():
    rope = Rope48("A")
    node = Node256(s=S.PLUS, k=K.RIGHT)
    rope.set(layer=2, position=5, node=node)
    assert rope.get(layer=2, position=5) is node

def test_push_fills_in_order():
    rope = Rope48("A")
    n1 = Node256(s=S.PLUS, k=K.RIGHT)
    n2 = Node256(s=S.MINUS, k=K.LEFT)
    rope.push(n1)
    rope.push(n2)
    assert rope.get(0, 0) is n1
    assert rope.get(0, 1) is n2

def test_push_raises_when_full():
    rope = Rope48("A")
    node = Node256(s=S.PLUS, k=K.RIGHT)
    for _ in range(LENGTH):
        rope.push(node)
    with pytest.raises(OverflowError):
        rope.push(node)

def test_closed_boundary_neighbor_wraps():
    rope = Rope48("A")
    first = Node256(s=S.PLUS, k=K.RIGHT)
    rope.set(0, 0, first)
    last_index = LENGTH - 1
    got = rope.neighbor(last_index, offset=1)
    assert got is first  # brzeg domknięty: ostatni sąsiaduje z pierwszym
