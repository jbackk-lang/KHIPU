from khipu.timdr import TIMDRValidator
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
