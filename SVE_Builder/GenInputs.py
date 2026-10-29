import os
import numpy as np
from .FilerReader import AbaqusMesh
from .WriteMooseInput import InplaneFile, OutplaneShearFile, OutofPlaneNormalFile

def process_regions(nodes, n_map, elements, e_map, e_types, elsets, nsets, BC, filedir, solver):
    output_dir = filedir
    if solver == 'linear':
        inFile = InplaneFile(nodes, n_map, elements, e_map, e_types, elsets, nsets, BC)
        inFile.create_files(output_dir, BC)
        outFile = OutplaneShearFile(nodes, n_map, elements, e_map, e_types, elsets, nsets, BC)
        outFile.create_files(output_dir, BC)
        outFile = OutofPlaneNormalFile(nodes, n_map, elements, e_map, e_types, elsets, nsets, BC)
        outFile.create_files(output_dir, BC)

def applyBCs(filedir, homo_name, solver, res, BC, i, j):

    outputdir = os.path.join(os.getcwd(), homo_name, f"Res{res}x{res}", f"Img{i}", f"SubImg{j}") 
    reader = AbaqusMesh(filedir)
    nodes = reader.get_nodes()
    elements = reader.get_elements()
    elsets = reader.get_elsets()
    nsets = reader.get_nsets()
    n_map = reader.nodeMap
    e_map = reader.elementMap
    e_types = reader.get_elem_type_map(elements)

    process_regions(
        nodes, n_map, 
        elements, e_map, e_types, 
        elsets, nsets, 
        BC, outputdir, solver
    )