import pytest

from khipu.node256 import Node256, S, K
from khipu.pipeline import SingleCPUSystem
from khipu.tetragon import TetragonSystem
from khipu.serialize import (
    node_to_dict, node_from_dict,
    lut256_to_dict, lut256_from_dict,
    rope256_to_dict, rope256_from_dict,
    rope48_to_dict, rope48_from_dict,
    single_cpu_system_to_dict, single_cpu_system_from_dict,
    tetragon_system_to_dict, tetragon_system_from_dict,
    save_json, load_json, save_pickle, load_pickle,
)


def test_node_round_trip():
    node = Node256(s=S.PLUS, k=K.RIGHT, idx=7)
    node.r = "R*"
    d = node_to_dict(node)
    restored = node_from_dict(d)
    assert restored == node
    assert restored is not node

def test_node_none_round_trip():
    assert node_to_dict(None) is None
    assert node_from_dict(None) is None

def test_lut256_round_trip():
    sys_ = SingleCPUSystem()
    sys_.feed_many([1, 2, 3, 12345, 65535, 0])
    d = lut256_to_dict(sys_.lut)
    restored = lut256_from_dict(d)
    assert len(restored) == len(sys_.lut)
    for idx in sys_.lut._table:
        assert restored._table[idx] == sys_.lut._table[idx]
        assert restored._table[idx] is not sys_.lut._table[idx]  # niezalezna kopia

def test_rope256_round_trip_preserves_sequence():
    sys_ = SingleCPUSystem()
    for w in [1, 2, 3, 12345, 65535, 0, 999]:
        sys_.feed(w)
    d = rope256_to_dict(sys_.rope)
    restored = rope256_from_dict(d)
    assert restored.screw_sequence() == sys_.rope.screw_sequence()
    assert restored.direction_sequence() == sys_.rope.direction_sequence()
    assert [n.r for n in restored.nodes] == [n.r for n in sys_.rope.nodes]

def test_rope48_round_trip_preserves_ring_state_after_wraparound():
    """60 push() na Rope48 dlugosci 48 - wymusza zawiniecie pierscienia,
    zeby sprawdzic ze write_cursor/total_pushed przezywaja round-trip,
    nie tylko tresc slotow."""
    t = TetragonSystem()
    for i in range(60):
        t.feed("A", i * 137)
    rope = t.ropes["A"]
    d = rope48_to_dict(rope)
    restored = rope48_from_dict(d)
    assert restored.total_pushed == rope.total_pushed == 60
    assert restored._write_cursor == rope._write_cursor
    assert [n.idx if n else None for n in restored.slots] == [n.idx if n else None for n in rope.slots]
    assert restored.filled_nodes() != [] and len(restored.filled_nodes()) == len(rope.filled_nodes())

def test_rope48_from_dict_rejects_wrong_slot_count():
    with pytest.raises(ValueError):
        rope48_from_dict({"name": "A", "slots": [None] * 10, "write_cursor": 0, "total_pushed": 0})

def test_single_cpu_system_round_trip_via_json(tmp_path):
    sys_ = SingleCPUSystem()
    for w in [1, 2, 3, 12345, 65535, 0, 999, 42]:
        sys_.feed(w)
    original_compressed = sys_.compress()

    path = tmp_path / "session.json"
    save_json(single_cpu_system_to_dict(sys_), str(path))
    loaded_dict = load_json(str(path))
    restored = single_cpu_system_from_dict(loaded_dict)

    assert restored.rope.screw_sequence() == sys_.rope.screw_sequence()
    assert len(restored.lut) == len(sys_.lut)
    assert restored.compress() == original_compressed
    # bufor klatek NIE jest przywracany (celowo, patrz serialize.py) - pusty po load
    assert len(restored.frames) == 0
    # ale dalsze feed() dziala normalnie na wznowionej sesji
    restored.feed(555)
    assert len(restored.rope) == len(sys_.rope) + 1

def test_single_cpu_system_from_dict_rejects_wrong_kind():
    with pytest.raises(ValueError):
        single_cpu_system_from_dict({"kind": "TetragonSystem"})

def test_tetragon_system_round_trip_via_json(tmp_path):
    t = TetragonSystem()
    for i, cpu in enumerate(["A", "B", "C", "D"] * 5):
        t.feed(cpu, (i + 1) * 4001)
    original_relations = t.axial_relations()

    path = tmp_path / "tetragon_session.json"
    save_json(tetragon_system_to_dict(t), str(path))
    restored = tetragon_system_from_dict(load_json(str(path)))

    assert restored.cpu_names == t.cpu_names
    for name in t.cpu_names:
        assert restored.ropes[name].filled_nodes() and len(restored.ropes[name].filled_nodes()) == len(t.ropes[name].filled_nodes())
        assert restored.ropes[name].total_pushed == t.ropes[name].total_pushed
    assert restored.axial_relations() == original_relations
    # dalsze feed() dziala normalnie
    restored.feed("A", 777)

def test_tetragon_system_round_trip_with_custom_cpu_names(tmp_path):
    t = TetragonSystem(cpu_names=("W", "X", "Y", "Z"))
    for i, cpu in enumerate(["W", "X", "Y", "Z"]):
        t.feed(cpu, (i + 1) * 4001)
    path = tmp_path / "custom_names.json"
    save_json(tetragon_system_to_dict(t), str(path))
    restored = tetragon_system_from_dict(load_json(str(path)))
    assert restored.cpu_names == ("W", "X", "Y", "Z")
    assert set(restored.axial_relations().keys()) == {"R_W_axis", "R_X_axis", "R_Y_axis", "R_Z_axis"}

def test_tetragon_system_from_dict_rejects_wrong_kind():
    with pytest.raises(ValueError):
        tetragon_system_from_dict({"kind": "SingleCPUSystem"})

def test_pickle_round_trip_single_cpu_system(tmp_path):
    sys_ = SingleCPUSystem()
    sys_.feed_many([1, 2, 3])
    path = tmp_path / "session.pkl"
    save_pickle(single_cpu_system_to_dict(sys_), str(path))
    restored_dict = load_pickle(str(path))
    restored = single_cpu_system_from_dict(restored_dict)
    assert restored.rope.screw_sequence() == sys_.rope.screw_sequence()
