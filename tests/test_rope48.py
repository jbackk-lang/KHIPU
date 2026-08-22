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

def test_push_wraps_and_overwrites_oldest_when_full():
    """NAPRAWIONY BUG: push() dawniej rzucal OverflowError po LENGTH
    wywolaniach (system trwale sie psul). Teraz jest to prawdziwy
    pierscien FIFO - po zapelnieniu nadpisuje najstarszy wpis, sznur
    zawsze ma dlugosc LENGTH, i mozna wolac push() bez ograniczen."""
    rope = Rope48("A")
    first = Node256(s=S.PLUS, k=K.RIGHT)
    rope.push(first)
    for _ in range(LENGTH - 1):
        rope.push(Node256(s=S.MINUS, k=K.LEFT))
    assert rope.get(0, 0) is first  # jeszcze nie nadpisany (dokladnie LENGTH pushy)

    overwritten = rope.push(Node256(s=S.PLUS, k=K.RIGHT))  # LENGTH+1-szy push
    assert overwritten is first          # najstarszy wpis zwrocony jako nadpisany
    assert rope.get(0, 0) is not first   # i faktycznie nadpisany w slocie
    assert len(rope) == LENGTH           # dlugosc sznura sie nie zmienia
    assert rope.total_pushed == LENGTH + 1


def test_push_never_raises_indefinitely():
    """Kontynuacja powyzszego: sznur dziala bez konca, nie tylko +1 push."""
    rope = Rope48("A")
    for i in range(LENGTH * 50):  # znacznie wiecej niz dawny limit 48
        rope.push(Node256(s=S.PLUS, k=K.RIGHT))
    assert rope.total_pushed == LENGTH * 50
    assert len(rope) == LENGTH

def test_closed_boundary_neighbor_wraps():
    rope = Rope48("A")
    first = Node256(s=S.PLUS, k=K.RIGHT)
    rope.set(0, 0, first)
    last_index = LENGTH - 1
    got = rope.neighbor(last_index, offset=1)
    assert got is first  # brzeg domknięty: ostatni sąsiaduje z pierwszym
