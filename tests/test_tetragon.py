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
