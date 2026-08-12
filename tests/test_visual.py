from khipu.visual import VisualEngine, FrameBuffer
from khipu.node256 import Node256, S, K

def test_project_produces_maps_same_length():
    engine = VisualEngine()
    nodes = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT)]
    frame = engine.project(nodes)
    assert len(frame.color_map) == len(nodes)
    assert len(frame.vector_map) == len(nodes)

def test_frame_buffer_respects_maxlen():
    fb = FrameBuffer(maxlen=2)
    engine = VisualEngine()
    for _ in range(5):
        fb.push(engine.project([Node256(s=S.PLUS, k=K.RIGHT)]))
    assert len(fb) == 2

def test_to_ascii_one_char_per_node():
    engine = VisualEngine()
    nodes = [Node256(s=S.PLUS, k=K.RIGHT), Node256(s=S.MINUS, k=K.LEFT)]
    frame = engine.project(nodes)
    assert len(frame.to_ascii()) == len(nodes)
