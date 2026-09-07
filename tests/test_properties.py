"""
Testy własnościowe (property-based, hypothesis) - dodane 2026-08.

Cel: 62 (teraz wiecej) recznie napisanych testow przykladowych w tym
repo NIE wylapaly dwoch realnych bledow znalezionych w tej sesji:
  1. aliasing obiektow w LUT256.lookup()/set() (patrz lut256.py,
     "POPRAWKA BLEDU ALIASINGU") - bo zaden test nie sprawdzal
     TOZSAMOSCI obiektow dla WIELU idx/wywolan naraz, tylko pojedyncze
     przyklady.
  2. martwy parametr `axis` w ResonanceFigure.axial_relations() (patrz
     axis.py, "NAPRAWIONA NIESPOJNOSC") - bo zaden test nie sprawdzal,
     ze WYNIK ZALEZY od stanu osi dla roznych/losowych kombinacji.

Testy wlasnosciowe generuja wiele losowych przypadkow i sprawdzaja
INWARIANTY (np. "zawsze niezalezne obiekty", "wynik zawsze zalezy od
X"), zamiast pojedynczych, recznie dobranych przykladow - co jest
dokladnie tym rodzajem testu, ktory mechanicznie wylapalby oba
powyzsze bledy, gdyby istnial wczesniej.

Wymaga `hypothesis` (opcjonalne - testy pomijaja sie, jesli brak paczki,
nie psuja reszty `pytest tests/`).
"""
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st

from khipu.node256 import Node256, S, K, D, B, W, L, R
from khipu.lut256 import LUT256
from khipu.cpu import CPUCore16
from khipu.gipu import GIPUIntegrator
from khipu.axis import NodeAxis, ResonanceFigure, TETRAGON_CPUS


# ---------------------------------------------------------------------
# 1. LUT256: lookup()/set() musza ZAWSZE zwracac niezalezne obiekty,
#    dla dowolnego idx i dowolnej liczby powtorzen - regresja dla
#    bledu aliasingu (klasy bledu, nie tylko jednego przypadku).
# ---------------------------------------------------------------------

@given(
    idx=st.integers(min_value=0, max_value=255),
    s=st.sampled_from(S.ALL),
    k=st.sampled_from(K.ALL),
    n_lookups=st.integers(min_value=2, max_value=20),
)
@settings(max_examples=100)
def test_lut256_lookup_always_returns_independent_objects(idx, s, k, n_lookups):
    lut = LUT256()
    nodes = [lut.lookup(idx, s=s, k=k) for _ in range(n_lookups)]
    # kazdy lookup() to INNY obiekt (nawet dla tego samego idx/s/k)
    ids = {id(n) for n in nodes}
    assert len(ids) == n_lookups
    # mutacja jednego nie wplywa na pozostale - porownanie z wartoscia
    # SPRZED mutacji (nie z literalem "R*", bo domyslny szablon danego
    # idx moze juz i tak miec r == "R*" - to nie byloby aliasingiem)
    original_r = [n.r for n in nodes]
    sentinel = "R*" if nodes[0].r != "R*" else "R0"
    nodes[0].r = sentinel
    for n, orig in zip(nodes[1:], original_r[1:]):
        assert n.r == orig


@given(
    idx=st.integers(min_value=0, max_value=255),
    s=st.sampled_from(S.ALL),
    k=st.sampled_from(K.ALL),
)
@settings(max_examples=100)
def test_lut256_set_stores_independent_copy_not_live_reference(idx, s, k):
    lut = LUT256()
    live = Node256(s=s, k=k, idx=idx)
    lut.set(idx, live)
    live.r = "R*"
    stored = lut.lookup(idx)
    assert stored is not live
    assert stored.r != "R*"


# ---------------------------------------------------------------------
# 2. GIPU.extend_relations(): dla dowolnego rosnacego sznura wezlow,
#    zaden wezel nie moze dzielic tozsamosci z innym (ogolniejsza
#    regresja dla tej samej klasy bledu, na poziomie calego pipeline'u
#    LUT->rope, nie tylko samego LUT256).
# ---------------------------------------------------------------------

@given(
    words=st.lists(st.integers(min_value=0, max_value=0xFFFF), min_size=1, max_size=60)
)
@settings(max_examples=50)
def test_extend_relations_never_aliases_nodes_across_positions(words):
    lut = LUT256()
    gipu = GIPUIntegrator()
    cpu = CPUCore16("CPU_TEST")
    nodes = []
    for w in words:
        s, k, idx = cpu.process_word(w)
        node = lut.lookup(idx, s=s, k=k)
        nodes.append(node)
        gipu.extend_relations(nodes)
    ids = [id(n) for n in nodes]
    assert len(set(ids)) == len(nodes)


# ---------------------------------------------------------------------
# 3. axial_relations(): wynik MUSI zalezec od stanu osi - regresja dla
#    bledu "martwy parametr axis". Generujemy dwa niezalezne, losowe
#    stany osi (przez losowe wezly CPU uzyte do axis.update()) i
#    sprawdzamy: albo wyniki sa rozne, albo oba stany osi byly (s,k)
#    identyczne (wtedy identyczny wynik jest poprawny, nie bledny).
# ---------------------------------------------------------------------

@given(
    node_s=st.sampled_from([s for s in S.ALL if s != S.ZERO]),
    node_k=st.sampled_from(K.ALL),
)
@settings(max_examples=100)
def test_axial_relations_depends_on_axis_state(node_s, node_k):
    """S0 wylaczone z wezlow CPU celowo: GIPU.relation_between() ma
    specjalny przypadek "ktorykolwiek wezel S0 -> zawsze R0", wiec taki
    wezel dawalby ten sam wynik NIEZALEZNIE od stanu osi - myliloby to
    test, ktorego celem jest sprawdzenie, ze oś JEST czytana."""
    fig = ResonanceFigure("tetragon")
    nodes = {c: Node256(s=node_s, k=node_k) for c in TETRAGON_CPUS}

    # oś w tym samym stanie co wezly CPU -> relacja musi byc REZONANS (R*)
    axis_same = NodeAxis()
    axis_same.update({c: Node256(s=node_s, k=node_k) for c in TETRAGON_CPUS})
    rel_same = fig.axial_relations(nodes, axis_same)
    assert all(v == "R*" for v in rel_same.values())

    # oś w stanie gwarantowanie ROZNYM (inny s, inny k, oba != S0) ->
    # relacja musi byc PRZECINAJACA (Rx), nigdy REZONANS
    other_s = next(s for s in S.ALL if s not in (node_s, S.ZERO))
    other_k = next(k for k in K.ALL if k != node_k)
    axis_diff = NodeAxis()
    axis_diff.update({c: Node256(s=other_s, k=other_k) for c in TETRAGON_CPUS})
    rel_diff = fig.axial_relations(nodes, axis_diff)
    assert all(v == "Rx" for v in rel_diff.values())

    assert rel_same != rel_diff


# ---------------------------------------------------------------------
# 4. Node256: dowolna kombinacja WARTOSCI Z WLASNYCH DOMEN (S.ALL,
#    K.ALL, ...) nigdy nie rzuca wyjatku; dowolna wartosc SPOZA domeny
#    ZAWSZE rzuca ValueError - sprawdzenie kompletnosci walidacji
#    __post_init__ (7 pol), nie tylko przykladow z recznych testow.
# ---------------------------------------------------------------------

@given(
    s=st.sampled_from(S.ALL), k=st.sampled_from(K.ALL), d=st.sampled_from(D.ALL),
    b=st.sampled_from(B.ALL), w=st.sampled_from(W.ALL), l=st.sampled_from(L.ALL),
    r=st.sampled_from(R.ALL),
)
@settings(max_examples=200)
def test_node256_accepts_any_combination_of_valid_domain_values(s, k, d, b, w, l, r):
    node = Node256(s=s, k=k, d=d, b=b, w=w, l=l, r=r)
    assert node.s == s and node.k == k


@given(bad_value=st.text(min_size=1, max_size=5).filter(lambda x: x not in S.ALL))
@settings(max_examples=50)
def test_node256_rejects_any_value_outside_s_domain(bad_value):
    with pytest.raises(ValueError):
        Node256(s=bad_value, k=K.RIGHT)


# ---------------------------------------------------------------------
# 5. detect_screw_batch: zgodnosc ze skalarna wersja dla DOWOLNEGO
#    word16 wygenerowanego przez hypothesis (uzupelnia test wyczerpujacy
#    i losowy z test_cpu_vectorized.py o strategie hypothesis, ktora
#    aktywnie szuka przypadkow brzegowych: 0, 0xFFFF, potegi 2, itd.)
# ---------------------------------------------------------------------

@given(word16=st.integers(min_value=0, max_value=0xFFFF))
@settings(max_examples=300)
def test_detect_screw_batch_matches_scalar_hypothesis(word16):
    assert CPUCore16.detect_screw_batch([word16])[0] == CPUCore16.detect_screw(word16)
