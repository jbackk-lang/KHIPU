"""
Testy dla oryginalnych, prostych modułów `node.py` / `rope.py` z katalogu
głównego repozytorium (format CTX/NODE do zapisu tekstowego, używany
przez `test.py`). `test.py` sam w sobie tylko drukował wynik bez żadnej
asercji — tutaj to samo zachowanie jest sprawdzone automatycznie.
"""
from node import Node
from rope import Rope


def test_roundtrip_preserves_context_and_count():
    rope = Rope("test_numbers")
    for pos, v in enumerate([10, 10, 10, 11, 11, 20]):
        rope.add_node(Node(color=64, twist="S", kind=0, distance=1, thickness=1, position=pos))

    encoded = rope.encode()
    decoded = Rope.decode(encoded)

    assert decoded.context == "test_numbers"
    assert len(decoded.nodes) == 6


def test_roundtrip_preserves_field_values():
    rope = Rope("ctx")
    rope.add_node(Node(color=200, twist="Z", kind=3, distance=7, thickness=2, position=0))

    decoded = Rope.decode(rope.encode())

    n = decoded.nodes[0]
    assert (n.color, n.twist, n.kind, n.distance, n.thickness, n.position) == (200, "Z", 3, 7, 2, 0)


def test_empty_rope_roundtrip():
    rope = Rope("empty")
    decoded = Rope.decode(rope.encode())
    assert decoded.context == "empty"
    assert decoded.nodes == []
