from khipu.gipu import GIPUIntegrator
from khipu.node256 import S, K, R, Node256

def test_relation_resonant_when_identical():
    g = GIPUIntegrator()
    a = Node256(s=S.PLUS, k=K.RIGHT)
    b = Node256(s=S.PLUS, k=K.RIGHT)
    assert g.relation_between(a, b) == R.RESONANT

def test_relation_independent_when_neutral():
    g = GIPUIntegrator()
    a = Node256(s=S.ZERO, k=K.PHI)
    b = Node256(s=S.PLUS, k=K.RIGHT)
    assert g.relation_between(a, b) == R.INDEPENDENT

def test_update_relations_closed_loop():
    g = GIPUIntegrator()
    nodes = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT), Node256(s=S.PLUS, k=K.RIGHT)]
    g.update_relations(nodes)
    # ostatni węzeł sąsiaduje z pierwszym (sznur domknięty)
    assert nodes[-1].r == g.relation_between(nodes[-1], nodes[0])

def test_update_lut_writes_back():
    from khipu.lut256 import LUT256
    g = GIPUIntegrator()
    lut = LUT256()
    node = lut.lookup(7, s=S.PLUS, k=K.RIGHT)
    node.r = R.RESONANT
    g.update_lut(lut, [node])
    assert lut.lookup(7).r == R.RESONANT

def test_distances_between_same_screw():
    g = GIPUIntegrator()
    nodes = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT), Node256(s=S.PLUS, k=K.RIGHT)]
    assert g.distances(nodes) == [2]
