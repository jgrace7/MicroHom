from .Nodes import NodeFactory, _2DNode, _3DNode
from .Elements import ElementFactory, CPS4, CPE4, C3D8, CPS3, CPE3

class AbaqusMesh:
    def __init__(self, filepath):
        self.filepath = filepath
        self.instance_name = None

    def get_nodes(self):
        nodes = {}
        with open(self.filepath, 'r') as file:
            read_nodes = False
            for line in file:
                upper_line = line.upper()
                if '*NODE' in upper_line:
                    read_nodes = True
                elif '*' in upper_line and read_nodes:
                    break 
                elif read_nodes:
                    parts = [float(val) for val in line.split(',') if val.strip()]
                    if len(parts) == 3:
                        node = NodeFactory.create_node(int(parts[0]), parts[1], parts[2])
                        nodes[node.id] = node
                    elif len(parts) == 4:
                        node = NodeFactory.create_node(int(parts[0]), parts[1], parts[2], parts[3])
                        nodes[node.id] = node
        return nodes

    def get_elements(self):
        elements = []
        with open(self.filepath, 'r') as file:
            ElementType = None
            for line in file:
                line_stripped = line.strip()
                upper_line = line_stripped.upper()

                if upper_line.startswith('*ELEMENT'):
                    ElementType = self._extract_element_type(line_stripped)

                elif ElementType and not upper_line.startswith('*'):
                    parts = [int(val) for val in line_stripped.split(',') if val.strip()]
                    if parts:
                        element_id, node_ids = parts[0], parts[1:]
                        elements.append(ElementFactory.create_element(ElementType, element_id, *node_ids))

                elif upper_line.startswith('*'):
                    ElementType = None  # reset
        return elements

    def _extract_element_type(self, line):

        parts = line.split('=')
        if len(parts) > 1:
            return parts[1].strip()
        return None

    def get_elsets(self):
        with open(self.filepath, 'r') as f:
            lines = [l.strip() for l in f]

        elsets = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.upper().startswith('*ELSET'):
                # Extract the name of the ELSET
                name = None
                parts = line.split(',')
                for part in parts:
                    if 'ELSET=' in part.upper():
                        name = part.split('=')[1].strip()
                        break
                if name is None:
                    name = f"elset_{len(elsets)+1}"

                elements = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('*'):
                    raw = lines[i].replace(" ", "").rstrip(',')
                    if raw:
                        tokens = raw.split(',')
                        nums = list(map(int, tokens))
                        elements.extend(nums)
                    i += 1

                elsets[name] = elements
            else:
                i += 1
        return elsets

    def get_nsets(self):
        with open(self.filepath, 'r') as f:
            lines = [l.strip() for l in f]

        nsets = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.upper().startswith('*NSET'):
                # Extract the name of the NSET
                name = None
                parts = line.split(',')
                for part in parts:
                    if 'NSET=' in part.upper():
                        name = part.split('=')[1].strip()
                        break
                if name is None:
                    name = f"nset_{len(nsets)+1}"

                nodes = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('*'):
                    parts = [p for p in lines[i].split(',') if p.strip()]
                    nums = list(map(int, parts))
                    if len(nums) == 3:
                        start, end, step = nums
                        nodes.extend(range(start, end + 1, step))
                    else:
                        nodes.extend(nums)
                    i += 1
                nsets[name] = nodes
            else:
                i += 1
        return nsets

    def nodeMap(self, nodes):
        n_map = {}
        for node in nodes.values():
            if isinstance(node, _2DNode):
                n_map[node.id] = (node.x, node.y)
            elif isinstance(node, _3DNode):
                n_map[node.id] = (node.x, node.y, node.z)
        return n_map

    def elementMap(self, elements):
        e_map = {}
        for element in elements:

            if isinstance(element, CPS4):
                e_map[element.id] = element.get_node_ids()
            elif isinstance(element, CPE4):
                e_map[element.id] = element.get_node_ids()
            elif isinstance(element, CPS3):
                e_map[element.id] = element.get_node_ids()
            elif isinstance(element, CPE3):
                e_map[element.id] = element.get_node_ids()
            elif isinstance(element, C3D8):
                e_map[element.id] = element.get_node_ids()
            else:
                raise TypeError(f"Unknown element type: {type(element)}")
        return e_map

    def get_elem_type_map(self, elms):
        type_map = {
            'CPS4': 'QUAD4',
            'CPE4': 'QUAD4',
            'CPS3': 'TRI3',
            'CPE3': 'TRI3',
            'C3D8': 'HEX8',
        }
        elem_type_map = {}
        for e in elms:
            name = type(e).__name__
            if name in type_map:
                elem_type_map[e.id] = type_map[name]
            else:
                raise TypeError(f"Unsupported element type: {name}")
        return elem_type_map