from node import Node

class Rope:
    def __init__(self, context):
        self.context = context
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def encode(self):
        lines = [f"CTX:{self.context}"]
        for n in self.nodes:
            lines.append(n.serialize())
        return "\n".join(lines)

    @staticmethod
    def decode(text):
        lines = text.split("\n")
        context = lines[0].split("CTX:")[1]
        rope = Rope(context)
        for line in lines[1:]:
            if line.strip():
                rope.add_node(Node.deserialize(line))
        return rope
