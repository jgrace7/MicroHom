class _2DNode:
    def __init__(self, node_id, x, y):
        self.id = node_id
        self.x = x
        self.y = y

    def __repr__(self):
        return f"2DNode({self.id}, {self.x}, {self.y})"

    def _get_dim(self):
        return '2D'

    def _get_coord(self):
        return self.x, self.y

class _3DNode:
    def __init__(self, node_id, x, y, z):
        self.id = node_id
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"3DNode({self.id}, {self.x}, {self.y}, {self.z})"

    def _get_dim(self):
        return '3D'

    def _get_coord(self):
        return self.x, self.y, self.z


class NodeFactory:
    @staticmethod
    def create_node(node_id, *coordinates):
        if len(coordinates) == 2:
            return _2DNode(node_id, *coordinates)
        elif len(coordinates) == 3:
            return _3DNode(node_id, *coordinates)
        else:
            raise ValueError("Invalid number of coordinates provided.")