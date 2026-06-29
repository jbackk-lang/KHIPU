from rope import Rope
from node import Node

rope = Rope("test_numbers")

values = [10, 10, 10, 11, 11, 20]
pos = 0

for v in values:
    node = Node(
        color=64,       # stan
        twist='S',      # rośnie
        kind=0,         # wartość
        distance=1,
        thickness=1,
        position=pos
    )
    rope.add_node(node)
    pos += 1

encoded = rope.encode()
print(encoded)

decoded = Rope.decode(encoded)
print(decoded.context, len(decoded.nodes))
