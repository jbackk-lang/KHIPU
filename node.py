class Node:
    def __init__(self, color, twist, kind, distance, thickness, position):
        self.color = color        # 0–255 (Λ)
        self.twist = twist        # 'S' or 'Z' (τ)
        self.kind = kind          # operator typu (ρ)
        self.distance = distance  # TRM
        self.thickness = thickness
        self.position = position

    def serialize(self):
        return f"{self.position}|{self.color}|{self.twist}|{self.kind}|{self.distance}|{self.thickness}"

    @staticmethod
    def deserialize(line):
        pos, col, tw, kind, dist, thick = line.split("|")
        return Node(
            color=int(col),
            twist=tw,
            kind=int(kind),
            distance=int(dist),
            thickness=int(thick),
            position=int(pos)
        )
