from khipu.axis import NodeAxis, ResonanceFigure, TRIANGLE_CPUS, TETRAGON_CPUS
from khipu.node256 import Node256, S, K
from khipu.gipu import GIPUIntegrator

def test_node_axis_majority_vote():
    axis = NodeAxis()
    nodes = {
        "A": Node256(s=S.PLUS, k=K.RIGHT),
        "B": Node256(s=S.PLUS, k=K.RIGHT),
        "C": Node256(s=S.MINUS, k=K.LEFT),
    }
    axis.update(nodes)
    assert axis.s_axis == S.PLUS  # 2 z 3 to S+

def test_propagate_delta_detects_change():
    axis = NodeAxis()
    assert axis.propagate_delta(S.PLUS, S.PLUS) is False
    assert axis.propagate_delta(S.PLUS, S.MINUS) is True

def test_triangle_has_three_edges_no_diagonals():
    fig = ResonanceFigure("triangle")
    assert len(fig.edges) == 3
    assert fig.diagonals == []
    assert fig.cpus == TRIANGLE_CPUS

def test_tetragon_has_four_edges_and_two_diagonals():
    fig = ResonanceFigure("tetragon")
    assert len(fig.edges) == 4
    assert len(fig.diagonals) == 2
    assert fig.cpus == TETRAGON_CPUS

def test_resonance_boost_ranges_match_docs():
    tri = ResonanceFigure("triangle")
    tet = ResonanceFigure("tetragon")
    assert tri.resonance_boost() == (0.15, 0.20)
    assert tet.resonance_boost() == (0.30, 0.40)

def test_axial_relations_covers_all_edges_and_diagonals():
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=S.PLUS, k=K.RIGHT) for c in TETRAGON_CPUS}
    axis = NodeAxis()
    axis.update(nodes)
    rel = fig.axial_relations(nodes, axis)
    assert len(rel) == 6  # 4 boki + 2 przekątne
