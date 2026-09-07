from khipu.tetragon import TetragonSystem

def test_capacity_matches_documentation():
    t = TetragonSystem()
    assert t.capacity_single_cpu() == 1536
    assert t.capacity_total() == 6144

def test_capacity_with_resonance_around_8000():
    t = TetragonSystem()
    lo, hi, mid = t.capacity_with_resonance()
    assert lo < 8000 < hi  # README.md: "~8000 stanów operacyjnych"

def test_feed_all_four_cpus():
    t = TetragonSystem()
    for i, cpu in enumerate(["A", "B", "C", "D"]):
        node = t.feed(cpu, (i + 1) * 4001)
        assert node.idx is not None

def test_axial_relations_available_after_feeding():
    """Naprawiono 2026-08: axial_relations() liczy teraz relację przez
    oś (hub-and-spoke, jedna na CPU), nie bezpośrednio CPU<->CPU (graf
    pełny) - patrz axis.py ResonanceFigure.axial_relations() docstring
    i ResonanceFigure.direct_relations() dla dawnego zachowania."""
    t = TetragonSystem()
    for i, cpu in enumerate(["A", "B", "C", "D"]):
        t.feed(cpu, (i + 1) * 4001)
    rel = t.axial_relations()
    assert set(rel.keys()) == {"R_A_axis", "R_B_axis", "R_C_axis", "R_D_axis"}

def test_direct_relations_still_available_via_figure():
    """Dawne zachowanie (relacja bezpośrednia CPU<->CPU, z pominięciem
    osi) jest nadal dostępne, jawnie, przez figure.direct_relations()."""
    t = TetragonSystem()
    for i, cpu in enumerate(["A", "B", "C", "D"]):
        t.feed(cpu, (i + 1) * 4001)
    rel = t.figure.direct_relations(t._last_nodes)
    assert set(rel.keys()) == {
        "R_AB", "R_BC", "R_CD", "R_DA", "R_AC", "R_BD",
    }

def test_rope_isometry_preserved_after_feeding():
    t = TetragonSystem()
    for w in range(20):
        t.feed("A", w * 137)
    assert t.ropes["A"].is_isometric()

def test_unknown_cpu_rejected():
    import pytest
    t = TetragonSystem()
    with pytest.raises(ValueError):
        t.feed("Z", 123)

def test_custom_cpu_names_figure_uses_matching_labels():
    """Regresja dla bledu naprawionego 2026-08 (patrz tetragon.py komentarz
    'UOGOLNIENIE NA DOWOLNE N CPU'): przed naprawa figura ZAWSZE uzywala
    etykiet A/B/C/D niezaleznie od faktycznych cpu_names, wiec
    axial_relations() dla wlasnych nazw zwracaloby puste/bledne wyniki
    (klucze figury nie pasowalyby do kluczy nodes_by_cpu)."""
    t = TetragonSystem(cpu_names=("W", "X", "Y", "Z"))
    assert t.figure.cpus == ("W", "X", "Y", "Z")
    for i, cpu in enumerate(["W", "X", "Y", "Z"]):
        t.feed(cpu, (i + 1) * 4001)
    rel = t.axial_relations()
    assert set(rel.keys()) == {"R_W_axis", "R_X_axis", "R_Y_axis", "R_Z_axis"}
    assert t.capacity_with_resonance() == t.capacity_with_resonance()  # nie rzuca (4 CPU -> tetragon boost)

def test_classifier_fn_propagates_to_all_cpus():
    """Regresja dla wtyczki DETECT_SCREW (2026-08): classifier_fn podany
    do TetragonSystem musi trafic do WSZYSTKICH CPU (sa 'identyczne')."""
    from khipu.node256 import S
    t = TetragonSystem(classifier_fn=lambda w: S.ZERO)
    for cpu in ["A", "B", "C", "D"]:
        node = t.feed(cpu, 999)
        assert node.s == S.ZERO

def test_five_cpu_tetragon_system_works_end_to_end():
    """N spoza 3/4 - TetragonSystem (mimo nazwy) obsluguje dowolne N,
    axial_relations() dziala, ale capacity_with_resonance() musi uczciwie
    odmowic (brak udokumentowanego wzoru boostu dla N=5)."""
    import pytest
    t = TetragonSystem(cpu_names=("A", "B", "C", "D", "E"))
    for i, cpu in enumerate(["A", "B", "C", "D", "E"]):
        t.feed(cpu, (i + 1) * 4001)
    rel = t.axial_relations()
    assert len(rel) == 5
    with pytest.raises(NotImplementedError):
        t.capacity_with_resonance()
