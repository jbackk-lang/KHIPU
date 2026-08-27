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

def test_direct_relations_covers_all_edges_and_diagonals():
    """Dawne zachowanie axial_relations() (graf pełny CPU<->CPU, z pominięciem
    osi) jest teraz jawnie nazwane direct_relations() - patrz axis.py."""
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=S.PLUS, k=K.RIGHT) for c in TETRAGON_CPUS}
    rel = fig.direct_relations(nodes)
    assert len(rel) == 6  # 4 boki + 2 przekątne


def test_axial_relations_one_per_cpu_not_per_edge():
    """axial_relations() naprawione: topologia gwiazdy = jedna relacja NA CPU
    (n), nie n(n-1)/2 jak graf pełny. Dla tetragonu: 4 relacje, nie 6."""
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=S.PLUS, k=K.RIGHT) for c in TETRAGON_CPUS}
    axis = NodeAxis()
    axis.update(nodes)
    rel = fig.axial_relations(nodes, axis)
    assert len(rel) == 4
    assert set(rel.keys()) == {"R_A_axis", "R_B_axis", "R_C_axis", "R_D_axis"}


def test_axial_relations_empty_before_axis_update():
    """Bez wcześniejszego axis.update() (s_axis/k_axis == None) nie ma
    z czego liczyć relacji przez oś - pusty wynik, nie wyjątek ani zgadywanie."""
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=S.PLUS, k=K.RIGHT) for c in TETRAGON_CPUS}
    axis = NodeAxis()  # brak update()
    assert fig.axial_relations(nodes, axis) == {}


def test_axial_relations_actually_depend_on_axis_state():
    """Regresja dla błędu 'axis param martwy' - mutacja stanu osi MUSI
    zmienić wynik axial_relations() (przed naprawą było to niemożliwe,
    bo axis nie było w ogóle czytane)."""
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=S.PLUS, k=K.RIGHT) for c in TETRAGON_CPUS}

    axis_same = NodeAxis()
    axis_same.update(nodes)  # większość S+/K> -> zgodne z węzłami CPU
    rel_same = fig.axial_relations(nodes, axis_same)
    assert all(v == "R*" for v in rel_same.values())  # ten sam s i k -> rezonans

    axis_diff = NodeAxis()
    axis_diff.update({c: Node256(s=S.MINUS, k=K.LEFT) for c in TETRAGON_CPUS})
    rel_diff = fig.axial_relations(nodes, axis_diff)
    assert rel_diff != rel_same
    assert all(v == "Rx" for v in rel_diff.values())  # inny s, inny k -> przecinające

    assert fig.axial_relations(nodes, axis_same) != fig.axial_relations(nodes, axis_diff)
