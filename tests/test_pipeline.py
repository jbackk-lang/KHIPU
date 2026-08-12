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
