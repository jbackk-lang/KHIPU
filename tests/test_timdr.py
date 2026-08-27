from khipu.timdr import TIMDRValidator, PHI
from khipu.node256 import S, K, Node256

def test_validate_pair_true_for_documented_mapping():
    t = TIMDRValidator()
    assert t.validate_pair(S.PLUS, K.RIGHT)
    assert not t.validate_pair(S.PLUS, K.LEFT)

def test_correct_fixes_inconsistent_pair():
    t = TIMDRValidator()
    s, k = t.correct(S.PLUS, K.LEFT)  # celowo złe K
    assert t.validate_pair(s, k)

def test_correct_leaves_consistent_pair_untouched():
    t = TIMDRValidator()
    s, k = t.correct(S.MINUS, K.LEFT)
    assert (s, k) == (S.MINUS, K.LEFT)

def test_rope_balance_perfect_half():
    t = TIMDRValidator()
    nodes = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT)]
    assert t.rope_balance(nodes) == 0.5
    assert t.validate_rope(nodes)

def test_rope_balance_extreme_violates_rule():
    t = TIMDRValidator(tolerance=0.1)
    nodes = [Node256(s=S.PLUS, k=K.RIGHT) for _ in range(10)]
    assert not t.validate_rope(nodes)

def test_default_tolerance_can_actually_reject_extreme_rope():
    """Regresja dla martwej tolerancji naprawionej 2026-08 (patrz
    docstring TIMDRValidator 'NAPRAWIONA TOLERANCJA MARTWA'): stara
    domyslna tolerancja phi-1~=0.618 byla WIEKSZA niz matematycznie
    mozliwe maksymalne odchylenie |balance-0.5|=0.5, wiec validate_rope()
    z DOMYSLNA tolerancja nie mogla NIGDY zwrocic False, niezaleznie od
    danych. Nowa domyslna tolerancja 2-phi~=0.382 < 0.5 faktycznie
    pozwala odrzucic skrajnie niezbalansowany sznur."""
    t = TIMDRValidator()  # domyslna tolerancja, bez recznego override
    assert t.tolerance < 0.5  # warunek konieczny, zeby reguła nie byla martwa

    balanced = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT)]
    assert t.validate_rope(balanced)  # balance=0.5, powinno przejsc

    extreme = [Node256(s=S.PLUS, k=K.RIGHT) for _ in range(100)]
    assert t.rope_balance(extreme) == 1.0
    assert not t.validate_rope(extreme)  # teraz faktycznie odrzucone

def test_old_default_tolerance_was_mathematically_vacuous():
    """Dokumentuje sam fakt matematycznej martwoty starej tolerancji
    (phi-1), niezaleznie od obecnego kodu - upewnia sie, ze to
    zrozumienie nie zgubi sie przy przyszlych zmianach."""
    old_tolerance = PHI - 1
    max_possible_deviation = 0.5
    assert old_tolerance > max_possible_deviation
