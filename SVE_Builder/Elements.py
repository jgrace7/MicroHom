from enum import Enum
from .Nodes import _2DNode, _3DNode

class ElementType(Enum):
    CPS4 = 'CPS4'
    CPE4 = 'CPE4'
    C3D8 = 'C3D8'
    CPS3 = 'CPS3'
    CPE3 = 'CPE3'

class CPS4:
    def __init__(self, element_id, n1, n2, n3, n4):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4

    def __repr__(self):
        return f"CPS4({self.id}, {self.n1}, {self.n2}, {self.n3}, {self.n4})"

    def get_element_type(self):
        return "CPS4"

    def dim(self):
        return '2D'

    def get_id(self):
        return self.id

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3, self.n4]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 4:
            raise ValueError("CPS4 must have exactly 4 node IDs.")
        self.n1, self.n2, self.n3, self.n4 = new_node_ids

    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        for node_id in [self.n1, self.n2, self.n3, self.n4]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
        centroid_x = x_sum / 4
        centroid_y = y_sum / 4
        return centroid_x, centroid_y


    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1]],
            [nodes[1], nodes[2]],
            [nodes[2], nodes[3]],
            [nodes[3], nodes[0]]
        ]

class CPS4R:
    def __init__(self, element_id, n1, n2, n3, n4):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4

    def __repr__(self):
        return f"CPS4R({self.id}, {self.n1}, {self.n2}, {self.n3}, {self.n4})"

    def get_element_type(self):
        return "CPS4R"

    def dim(self):
        return '2D'

    def get_id(self):
        return self.id

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3, self.n4]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 4:
            raise ValueError("CPS4 must have exactly 4 node IDs.")
        self.n1, self.n2, self.n3, self.n4 = new_node_ids

    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1]],
            [nodes[1], nodes[2]],
            [nodes[2], nodes[3]],
            [nodes[3], nodes[0]]
        ]
    
    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        for node_id in [self.n1, self.n2, self.n3, self.n4]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
        centroid_x = x_sum / 4
        centroid_y = y_sum / 4
        return centroid_x, centroid_y

class CPE4:
    def __init__(self, element_id, n1, n2, n3, n4):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4

    def __repr__(self):
        return f"CPE4({self.id}, {self.n1}, {self.n2}, {self.n3}, {self.n4})"

    def get_id(self):
        return self.id

    def get_element_type(self):
        return "CPE4"

    def dim(self):
        return '2D'

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3, self.n4]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 4:
            raise ValueError("CPE4 must have exactly 4 node IDs.")
        self.n1, self.n2, self.n3, self.n4 = new_node_ids

    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        for node_id in [self.n1, self.n2, self.n3, self.n4]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
        centroid_x = x_sum / 4
        centroid_y = y_sum / 4
        return centroid_x, centroid_y

    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1]],
            [nodes[1], nodes[2]],
            [nodes[2], nodes[3]],
            [nodes[3], nodes[0]]
        ]

class CPE3:
    def __init__(self, element_id, n1, n2, n3):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __repr__(self):
        return f"CPE3({self.id}, {self.n1}, {self.n2}, {self.n3})"

    def get_element_type(self):
        return "CPE3"

    def dim(self):
        return '2D'

    def get_id(self):
        return self.id

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 3:
            raise ValueError("CPE3 must have exactly 3 node IDs.")
        self.n1, self.n2, self.n34 = new_node_ids

    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        for node_id in [self.n1, self.n2, self.n3]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
        centroid_x = x_sum / 3
        centroid_y = y_sum / 3
        return centroid_x, centroid_y

    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1]],
            [nodes[1], nodes[2]],
            [nodes[2], nodes[0]],
        ]
 
class CPS3:
    def __init__(self, element_id, n1, n2, n3):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __repr__(self):
        return f"CPS3({self.id}, {self.n1}, {self.n2}, {self.n3})"

    def get_element_type(self):
        return "CPS3"

    def dim(self):
        return '2D'

    def get_id(self):
        return self.id

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 3:
            raise ValueError("CPS3 must have exactly 3 node IDs.")
        self.n1, self.n2, self.n34 = new_node_ids

    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        for node_id in [self.n1, self.n2, self.n3]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
        centroid_x = x_sum / 3
        centroid_y = y_sum / 3
        return centroid_x, centroid_y

    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1]],
            [nodes[1], nodes[2]],
            [nodes[2], nodes[0]],
        ]
 
class C3D8:
    def __init__(self, element_id, n1, n2, n3, n4, n5, n6, n7, n8):
        self.id = element_id
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.n5 = n5
        self.n6 = n6
        self.n7 = n7
        self.n8 = n8

    def __repr__(self):
        return f"C3D8({self.id}, {self.n1}, {self.n2}, {self.n3}, {self.n4}," \
               f" {self.n5}, {self.n6}, {self.n7}, {self.n8})"

    def get_id(self):
        return self.id

    def get_element_type(self):
        return "C3D8"

    def dim(self):
        return '3D'

    def get_node_ids(self):
        return [self.n1, self.n2, self.n3, self.n4, self.n5, self.n6, self.n7, self.n8]

    def update_node_ids(self, new_node_ids):
        if len(new_node_ids) != 8:
            raise ValueError("C3D8 must have exactly 8 node IDs.")
        self.n1, self.n2, self.n3, self.n4, self.n5, self.n6, self.n7, self.n8 = new_node_ids

    def calculate_boundary(self):
        nodes = self.get_node_ids()
        return [
            [nodes[0], nodes[1], nodes[2], nodes[3]],
            [nodes[4], nodes[7], nodes[6], nodes[5]],
            [nodes[0], nodes[4], nodes[5], nodes[1]],
            [nodes[1], nodes[5], nodes[6], nodes[2]],
            [nodes[2], nodes[6], nodes[7], nodes[3]],
            [nodes[3], nodes[7], nodes[4], nodes[0]]
        ]
    
    def calculate_centroid(self, nodes):
        """
        Calculate the centroid of the 3D element based on the nodes.
        """
        x_sum = 0
        y_sum = 0
        z_sum = 0
        for node_id in [self.n1, self.n2, self.n3, self.n4, self.n5, self.n6, self.n7, self.n8]:
            node = nodes[node_id]
            x_sum += node.x
            y_sum += node.y
            z_sum += node.z
        centroid_x = x_sum / 8
        centroid_y = y_sum / 8
        centroid_z = z_sum / 8
        return centroid_x, centroid_y, centroid_z
    

class ElementFactory:
    @staticmethod
    def create_element(element_type, element_id, *node_ids):

        # Convert string identifiers to the ElementType enum if necessary
        if isinstance(element_type, str):
            element_type = ElementType[element_type]

        # Now check against the ElementType enum
        if element_type == ElementType.CPS4 and len(node_ids) == 4:
            return CPS4(element_id, *node_ids)
        elif element_type == ElementType.CPE4 and len(node_ids) == 4:
            return CPE4(element_id, *node_ids)
        elif element_type == ElementType.C3D8 and len(node_ids) == 8:
            return C3D8(element_id, *node_ids)
        elif element_type == ElementType.CPS3 and len(node_ids) == 3:
            return CPS3(element_id, *node_ids)
        elif element_type == ElementType.CPE3 and len(node_ids) == 3:
            return CPS3(element_id, *node_ids)
        else:
            raise ValueError(f"Invalid type or number of node references for {element_type}.")
