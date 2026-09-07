from khipu.pipeline import SingleCPUSystem

def test_feed_grows_rope():
    sys_ = SingleCPUSystem()
    sys_.feed(1234)
    sys_.feed(5678)
    assert len(sys_.rope) == 2

def test_feed_creates_frame():
    sys_ = SingleCPUSystem()
    sys_.feed(1234)
    assert sys_.frames.latest() is not None

def test_rope_direction_consistency_after_timdr():
    sys_ = SingleCPUSystem()
    for w in range(0, 5000, 137):
        sys_.feed(w)
    assert sys_.rope.is_direction_consistent()

def test_compress_never_grows_output():
    sys_ = SingleCPUSystem()
    for w in range(0, 5000, 137):
        sys_.feed(w)
    compressed = sys_.compress()
    assert len(compressed) <= len(sys_.rope)

def test_feed_many_matches_feed_loop():
    sys_ = SingleCPUSystem()
    a = sys_.feed_many([1, 2, 3])
    assert len(a) == 3
    assert len(sys_.rope) == 3


def test_feed_stream_yields_same_nodes_as_feed_many():
    """feed_stream() musi dawac te same wyniki co feed_many(), tylko
    strumieniowo (generator) zamiast listy naraz."""
    words = [1, 2, 3, 4, 5]
    sys_many = SingleCPUSystem()
    many_result = sys_many.feed_many(words)

    sys_stream = SingleCPUSystem()
    stream_result = list(sys_stream.feed_stream(words))

    assert len(stream_result) == len(many_result) == len(words)
    for a, b in zip(many_result, stream_result):
        assert (a.s, a.k, a.idx) == (b.s, b.k, b.idx)
    assert len(sys_stream.rope) == len(words)


def test_feed_stream_is_lazy_generator():
    """feed_stream() zwraca generator - nic nie przetwarza, dopoki nie
    zaczniemy iterowac (rozne od feed_many(), ktore przetwarza od razu)."""
    import types
    sys_ = SingleCPUSystem()
    gen = sys_.feed_stream([1, 2, 3])
    assert isinstance(gen, types.GeneratorType)
    assert len(sys_.rope) == 0  # nic jeszcze nie przetworzone
    next(gen)
    assert len(sys_.rope) == 1  # dokladnie jeden element przetworzony


def test_feed_stream_works_with_arbitrary_iterable_not_just_list():
    """Generator wejsciowy (nie tylko lista) - kluczowa roznica wobec
    feed_many(), ktore i tak zbiera wszystko do listy na starcie."""
    sys_ = SingleCPUSystem()

    def word_generator():
        for w in range(10):
            yield w * 137

    result = list(sys_.feed_stream(word_generator()))
    assert len(result) == 10
    assert len(sys_.rope) == 10


def test_custom_classifier_fn_is_actually_used():
    """Regresja dla wtyczki DETECT_SCREW (2026-08): wlasny classifier_fn
    musi byc faktycznie uzywany przez cala pipeline (feed()), nie tylko
    przyjety i zignorowany."""
    from khipu.node256 import S

    calls = []

    def always_zero(word16):
        calls.append(word16)
        return S.ZERO

    sys_ = SingleCPUSystem(classifier_fn=always_zero)
    node = sys_.feed(12345)
    assert calls == [12345]
    assert node.s == S.ZERO


def test_custom_classifier_fn_bad_return_value_raises_clearly():
    """classifier_fn zwracajacy cos spoza S.ALL musi ujawnic sie od razu,
    czytelnym bledem, nie gdzies gleboko w Node256/LUT256."""
    import pytest

    def broken(word16):
        return "NIE_TAKIE_S"

    sys_ = SingleCPUSystem(classifier_fn=broken)
    with pytest.raises(ValueError):
        sys_.feed(1)


def test_default_classifier_unchanged_when_none_passed():
    """Bez podania classifier_fn, zachowanie identyczne jak przed dodaniem
    tej opcji (domyslny detect_screw)."""
    from khipu.cpu import CPUCore16
    sys_ = SingleCPUSystem()
    for w in [0, 1, 255, 4096, 32768, 65535]:
        assert sys_.cpu.classify(w) == CPUCore16.detect_screw(w)
