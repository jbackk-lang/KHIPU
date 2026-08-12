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
    t = TetragonSystem()
    for i, cpu in enumerate(["A", "B", "C", "D"]):
        t.feed(cpu, (i + 1) * 4001)
    rel = t.axial_relations()
    assert set(rel.keys()) == {
        "R_AB_axis", "R_BC_axis", "R_CD_axis", "R_DA_axis",
        "R_AC_axis", "R_BD_axis",
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
