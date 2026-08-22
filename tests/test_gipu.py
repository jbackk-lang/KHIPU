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

def test_extend_relations_matches_full_recompute_open_chain():
    """extend_relations() (szybka, przyrostowa) musi dawac te same relacje
    co pelne przeliczenie BEZ zawijania (otwarty lancuch, nie zamkniety
    cykl) - to jest wlasnie roznica wobec update_relations()."""
    g = GIPUIntegrator()
    nodes = [
        Node256(s=S.PLUS, k=K.RIGHT),
        Node256(s=S.PLUS, k=K.RIGHT),
        Node256(s=S.MINUS, k=K.LEFT),
        Node256(s=S.PLUS, k=K.RIGHT),
    ]
    # symuluj to, co robi SingleCPUSystem.feed(): extend_relations po KAZDYM dodaniu
    grown = []
    for n in nodes:
        grown.append(n)
        g.extend_relations(grown)

    # referencja: otwarty lancuch bez zawijania, policzony od zera na koncu
    expected = [R.INDEPENDENT] * len(nodes)
    for i in range(len(nodes) - 1):
        expected[i] = g.relation_between(nodes[i], nodes[i + 1])

    assert [n.r for n in nodes] == expected
    # i NIE rownaja sie zamknietemu cyklowi (ostatni->pierwszy), bo to otwarty sznur:
    assert nodes[-1].r == R.INDEPENDENT


def test_extend_relations_is_o1_per_call_not_quadratic():
    """Dowod wydajnosciowy: liczba wywolan relation_between() na jedno
    dodanie wezla musi byc stala (1), niezaleznie od dlugosci sznura -
    inaczej update_relations() (pelne, O(n)) zamiast extend_relations()."""
    g = GIPUIntegrator()
    calls = {"n": 0}
    orig = g.relation_between
    def counting(a, b):
        calls["n"] += 1
        return orig(a, b)
    g.relation_between = counting

    grown = []
    for _ in range(500):
        grown.append(Node256(s=S.PLUS, k=K.RIGHT))
        calls["n"] = 0
        g.extend_relations(grown)
        assert calls["n"] <= 1  # co najwyzej jedno porownanie na dodany wezel

