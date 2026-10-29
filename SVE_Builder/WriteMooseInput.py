# 2D workflow
import os, re

class InplaneFile:
    EXT = ".inp"    
    FILE_DIR = "ModelFiles/Model_files_IN"
    INPUT = 'input.i'

    def __init__(self, nodes, n_map, elements, e_map, e_types, elsets, nsets, BC):
        self.ns = nodes
        self.elms = elements
        self.elsets = elsets
        self.nsets = nsets
        self.e_map = e_map
        self.e_types = e_types
        self.n_map = n_map
        self.BC = BC

    # make sure there is a place to put the input file.
    def make_SVE_dir(self, dir, i):
        sve_dir = os.path.join(dir, f"SVE{i}")
        os.makedirs(sve_dir, exist_ok=True)

    # Specifying the geo to use in the input file
    def write_mesh_block(self, dir, i):
        mesh_path = os.path.join(dir, "Micro.inp").replace(f"RESULTS_linear", "RESULTS_OOF")
        #mesh_path = os.path.join(dir, "Micro.inp")

        with open(os.path.join(self.FILE_DIR, "MESH.i")) as f:
            content = f.read().replace("{{MESH_FILENAME}}", mesh_path)
        
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "w") as f:
            f.write(content)
            f.write("\n")

    # Writing Global Params Block
    def write_params_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "GlobalParams.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_physics_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Physics.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def get_phase_type_pairs(self):
        pairs = set()
        for phase, element_ids in self.elsets.items():
            for eid in element_ids:
                etype = self.e_types.get(eid)
                if etype:
                    pairs.add((phase, etype))
        return sorted(pairs)

    def render_material_block(self, phase, elem_type, props):
        with open(os.path.join(self.FILE_DIR, "Materials.i")) as t:
            temp = t.read()
            phase_label = f"{phase}_{elem_type}"
            temp = temp.replace("{{PHASE}}", phase_label)
            temp = temp.replace("{{ETYPE}}", elem_type)
            temp = temp.replace("{{BLOCK}}", phase_label)


            if props['model'] == 'iso':
                with open(os.path.join(self.FILE_DIR, "Elasticity_iso.i")) as et:
                    heat = et.read()
                heat = heat.replace("{{PHASE}}", phase_label)
                heat = heat.replace("{{BLOCK}}", phase_label)
                heat = heat.replace("{{E}}", str(props['E']))
                heat = heat.replace("{{NU}}", str(props['nu']))
            elif props['model'] == 'transverse':
                with open(os.path.join(self.FILE_DIR, "Elasticity_transverse.i")) as et:
                    heat = et.read()
                heat = heat.replace("{{PHASE}}", phase_label)
                heat = heat.replace("{{BLOCK}}", phase_label)
                for key in ['C11', 'C12', 'C13', 'C33', 'C44']:
                    heat = heat.replace(f"{{{{{key}}}}}", str(props[key]))
            else:
                raise ValueError(f"Unknown elasticity model: {props['model']}")
            
            temp = temp.replace("{{ELASTICITY_BLOCK}}", heat)

            return temp 
        
    def write_materials_block(self, dir, i):
        import json
        
        # Load properties from config
        with open("config.json", "r") as f:
            config = json.load(f)
        
        json_props = config.get("materials", {})

        def iso_C(E, nu):
            return {'model': 'iso', 'E': E, 'nu': nu}

        def transversely_iso_C(E_L, E_T, nu_LT, nu_TT, G_LT):
            delta = E_L/(2*(1-nu_TT)*(E_L/E_T) - 4*nu_LT**2)
            C11 = delta + E_T/(2*(1+nu_TT))
            C12 = delta - E_T/(2*(1+nu_TT))
            C13 = 2*delta*nu_LT
            C33 = E_L + 4*delta*nu_LT**2
            C44 = G_LT
            return {'model': 'transverse', 'C11': C11, 'C12': C12, 'C13': C13, 'C33': C33, 'C44': C44}
        
        props_map = {}
        for phase, mat in json_props.items():
            if mat["model"] == "iso":
                props_map[phase] = iso_C(mat["E"], mat["nu"])
            elif mat["model"] == "transverse":
                props_map[phase] = transversely_iso_C(mat["E_L"], mat["E_T"], mat["nu_LT"], mat["nu_TT"], mat["G_LT"])

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        pairs = self.get_phase_type_pairs()

        with open(out_path, "a") as f:
            f.write("[Materials]\n")
            for phase, elem_type in pairs:
                props = props_map.get(phase)
                if props:
                    block = self.render_material_block(phase, elem_type, props)
                    f.write(block)
            with open(os.path.join(self.FILE_DIR, "stress.i")) as t:
                f.write(t.read())
            f.write("\n[]\n\n")

    def write_BCs_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, f"{BC}_{i}.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_Exec_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, "Exec.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_Output_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Outputs.i")) as f:
            content = f.read()

        output_base = os.path.join(dir, f"SVE{i}", f"input")
        content = content.replace("{{EXODUS_FILENAME}}", output_base)
        content = content.replace("{{CSV_FILENAME}}", output_base)

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def render_postprocess_block(self, phase, blocks, vars):
        out = ""

        with open(os.path.join(self.FILE_DIR, "volume.i")) as vt:
            volume_temp = vt.read()
        volume_temp = volume_temp.replace("{{PHASE}}", phase)
        volume_temp = volume_temp.replace("{{BLOCKS}}", ' '.join(blocks))
        out += volume_temp + "\n"

        for var in vars:
            with open(os.path.join(self.FILE_DIR, "PostProcess.i")) as t:
                temp = t.read()
            temp = temp.replace("{{PHASE}}", phase)
            temp = temp.replace("{{VAR}}", var)
            temp = temp.replace("{{BLOCKS}}", ' '.join(blocks))
            out += temp + "\n"
        return out

    def write_processing_block(self, dir, i):
        # 1. Define Standard Vars (Stress/Strain)
        vars = ['stress_xx', 'stress_yy', 'stress_xy',
                'strain_xx', 'strain_yy', 'strain_xy']

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)

        # 2. Pre-load Templates
        # Load the new C-Tensor template
        c_template_path = os.path.join(self.FILE_DIR, "PostProcessC.i")
        with open(c_template_path, 'r') as t:
            c_template_content = t.read()
            
        # Load the static Global variables template (PostProcess2.i)
        pp2_path = os.path.join(self.FILE_DIR, "PostProcess2.i")
        with open(pp2_path, 'r') as t:
            pp2_content = t.read()

        # 3. Aggregate mesh blocks per phase
        # This logic is vital because it resolves 'Matrix' -> 'Matrix_HEX8'
        phase_blocks = {}
        for phase, elem_ids in self.elsets.items():
            # Skip non-material sets
            if phase.lower() in ['all', 'nodes']: 
                continue

            for eid in elem_ids:
                etype = self.e_types.get(eid)
                if etype:
                    phase_blocks.setdefault(phase, set()).add(f"{phase}_{etype}")

        # 4. Write the Single Combined Block
        with open(out_path, "a") as f:
            f.write("[Postprocessors]\n")
            
            # Loop through each phase (Matrix, Yarn, etc.)
            for phase, blocks_set in phase_blocks.items():
                # specific blocks string for MOOSE: "Matrix_HEX8 Matrix_TET4"
                blocks_str = " ".join(sorted(blocks_set))
                
                # --- A. Standard Stress/Strain (Existing) ---
                # Uses your helper function to render PostProcess.i for 'vars'
                block_content = self.render_postprocess_block(phase, sorted(blocks_set), vars)
                f.write(block_content)
                
                # --- B. C-Tensor Averages (New Merged Logic) ---
                # Uses the hardcoded PostProcess_C.i template
                c_chunk = c_template_content.replace("{{PHASE}}", phase)
                c_chunk = c_chunk.replace("{{BLOCKS}}", blocks_str)
                f.write("\n" + c_chunk + "\n")

            # --- C. Global Static Content ---
            # Append the contents of PostProcess2.i (e.g., global averages)
            f.write("\n" + pp2_content + "\n")

            # Close the Postprocessors block
            f.write("[]\n\n")

    def centroid(self, nodes, nsets):
        pts = {k: nodes[nsets[k][0]] for k in ['bottomleft', 'bottomright', 'topleft', 'topright'] if k in nsets and nsets[k]}
        if len(pts) < 3:
            raise ValueError("Not enough points")
        xs = [pt.x for pt in pts.values()]
        ys = [pt.y for pt in pts.values()]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        lx = abs(pts['bottomright'].x - pts['bottomleft'].x) if 'bottomright' in pts and 'bottomleft' in pts else 1.0
        ly = abs(pts['topleft'].y - pts['bottomleft'].y) if 'topleft' in pts and 'bottomleft' in pts else 1.0
        return (cx, cy)
 
    def write_BcsFunc_block(self, dir, i, centroid, BC):
        if BC == "trac":
            pass
        else:    
            x_centroid, y_centroid = centroid

            with open(os.path.join(self.FILE_DIR, f"Func_{BC}_{i}.i")) as f:
                template = f.read()

            # Replace placeholders
            template = template.replace("{{XC}}", str(x_centroid))
            template = template.replace("{{YC}}", str(y_centroid))

            out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
            with open(out_path, "a") as f:
                f.write(template)
                f.write("\n")

    def write_aux_vars_block(self, dir, i):
        """
        Writes the AuxVariables block.
        FIX: Aggregates element types to form the correct block string (e.g., 'grey_TRI3 grey_QUAD4').
        """
        template_path = os.path.join(self.FILE_DIR, "AuxVariables.i")
        with open(template_path, 'r') as t:
            template_content = t.read()

        block_content = ""
        
        for phase_name, elem_ids in self.elsets.items():
            if phase_name.lower() in ['all', 'nodes']: 
                continue
            
            # --- FIX START: Find all element types for this phase ---
            found_types = set()
            for eid in elem_ids:
                etype = self.e_types.get(eid)
                if etype:
                    found_types.add(etype)
            
            # Construct the MOOSE block list string: "grey_TRI3 grey_QUAD4"
            valid_blocks = [f"{phase_name}_{t}" for t in sorted(found_types)]
            blocks_str = " ".join(valid_blocks)
            # --- FIX END ---

            if not blocks_str:
                continue

            chunk = template_content.replace("{{PHASE}}", phase_name)
            chunk = chunk.replace("{{BLOCKS}}", blocks_str) 
            block_content += chunk + "\n"

        sve_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        with open(sve_path, "a") as f:
            f.write("\n[AuxVariables]\n")
            f.write(block_content)
            f.write("[]\n")

    def write_aux_kernels_block(self, dir, i):
        """
        Writes the AuxKernels block using the hardcoded template.
        """
        template_path = os.path.join(self.FILE_DIR, "AuxKernels.i")
        with open(template_path, 'r') as t:
            template_content = t.read()

        block_content = ""

        for phase_name in self.elsets.keys():
            if phase_name.lower() in ['all', 'nodes']: 
                continue

            chunk = template_content.replace("{{PHASE}}", phase_name)
            # No need for {{BLOCKS}} in AuxKernels usually, just the variable name
            block_content += chunk + "\n"

        sve_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        with open(sve_path, "a") as f:
            f.write("\n[AuxKernels]\n")
            f.write(block_content)
            f.write("[]\n")

    def create_files(self, dir, BC):
        for i in range(3):
            sve_path = os.path.join(dir, f"SVE{i}", self.INPUT)
            if os.path.exists(sve_path):
                os.remove(sve_path)  # Clear existing input file to avoid double appending

            self.make_SVE_dir(dir, i)
            self.write_mesh_block(dir, i)
            self.write_aux_vars_block(dir, i)
            self.write_aux_kernels_block(dir, i)
            self.write_params_block(dir, i)
            self.write_physics_block(dir, i)
            self.write_materials_block(dir, i)
            self.write_BCs_block(dir, i, BC)
            self.write_Exec_block(dir, i, BC)
            self.write_Output_block(dir, i)
            self.write_processing_block(dir, i)
            c = self.centroid(self.ns, self.nsets)
            self.write_BcsFunc_block(dir, i, c, BC)

class OutplaneShearFile:
    EXT = ".inp"    
    FILE_DIR = "ModelFiles/Model_files_OUT_SHEAR"
    INPUT = 'input.i'

    def __init__(self, nodes, n_map, elements, e_map, e_types, elsets, nsets, BC):
        self.ns = nodes
        self.elms = elements
        self.elsets = elsets
        self.nsets = nsets
        self.e_map = e_map
        self.e_types = e_types
        self.n_map = n_map
        self.BC = BC

    def make_SVE_dir(self, dir, i):
        sve_dir = os.path.join(dir, f"SVE{i}")
        os.makedirs(sve_dir, exist_ok=True)

    def write_mesh_block(self, dir, i):
        mesh_path = os.path.join(dir, "Micro.inp").replace(f"RESULTS_linear", "RESULTS_OOF")
        #mesh_path = os.path.join(dir, "Micro.inp")


        with open(os.path.join(self.FILE_DIR, "MESH.i")) as f:
            content = f.read().replace("{{MESH_FILENAME}}", mesh_path)
        
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "w") as f:
            f.write(content)
            f.write("\n")

    def write_var_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Variables.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_kernel_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Kernel.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def get_phase_type_pairs(self):
        pairs = set()
        for phase, element_ids in self.elsets.items():
            for eid in element_ids:
                etype = self.e_types.get(eid)
                if etype:
                    pairs.add((phase, etype))
        return sorted(pairs)

    def render_material_block(self, phase, elem_type, props):
        with open(os.path.join(self.FILE_DIR, "Materials.i")) as t:
            temp = t.read()
            phase_label = f"{phase}_{elem_type}"
            temp = temp.replace("{{PHASE}}", phase_label)
            temp = temp.replace("{{ETYPE}}", elem_type)
            temp = temp.replace("{{BLOCK}}", phase_label)

            if props['model'] == 'iso':
                with open(os.path.join(self.FILE_DIR, "IsoHeat.i")) as t:
                    heat = t.read()
                heat = heat.replace("{{PHASE}}", phase_label)
                heat = heat.replace("{{BLOCK}}", phase_label)
                heat = heat.replace("{{G}}", str(props['G']))

            elif props['model'] == 'trans_iso':
                with open(os.path.join(self.FILE_DIR, "TransIsoHeat.i")) as t:
                    heat = t.read()
                heat = heat.replace("{{PHASE}}", phase_label)
                heat = heat.replace("{{BLOCK}}", phase_label)
                for key in ['Kxx', 'Kxy', 'Kxz', 'Kyx', 'Kyy', 'Kyz', 'Kzx', 'Kzy', 'Kzz']:
                #for key in ['Kxx', 'Kxy', 'Kyx', 'Kyy']:
                    heat = heat.replace(f"{{{{{key}}}}}", str(props[key]))
            else:
                raise ValueError(f"Unknown heat model: {props['model']}")

            temp = temp.replace("{{ELASTICITY_BLOCK}}", heat)

        return temp + "\n"

    def write_materials_block(self, dir, i):
        import json
        
        # Load properties from config
        with open("config.json", "r") as f:
            config = json.load(f)
        
        json_props = config.get("materials", {})

        def iso_G(E, nu):
            G = E / (2 * (1 + nu))
            return {
                'model': 'iso',
                'G': G
            }

        def trans_iso_G(E_L, E_T, nu_LT, nu_TT, G_LT):
            return {
                'model': 'trans_iso',
                'Kxx': G_LT, 'Kxy': 0.0, 'Kxz': 0.0,
                'Kyx': 0.0, 'Kyy': G_LT, 'Kyz': 0.0,
                'Kzx': 0.0, 'Kzy': 0.0, 'Kzz': 0.0
            }
        
        props_map = {}
        for phase, mat in json_props.items():
            if mat["model"] == "iso":
                props_map[phase] = iso_G(mat["E"], mat["nu"])
            elif mat["model"] == "transverse":
                props_map[phase] = trans_iso_G(
                    mat["E_L"], mat["E_T"], mat["nu_LT"], mat["nu_TT"], mat["G_LT"]
                )

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        pairs = self.get_phase_type_pairs()

        with open(out_path, "a") as f:
            f.write("[Materials]\n")
            for phase, elem_type in pairs:
                props = props_map.get(phase)
                if props:
                    block = self.render_material_block(phase, elem_type, props)
                    f.write(block)
            f.write("\n[]\n\n")

    def write_auxVar_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "AuxVars.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_auxKer_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "AuxKernels.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_BCs_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, f"{BC}_{i}.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_Exec_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, "Exec.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_Output_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Outputs.i")) as f:
            content = f.read()

        output_base = os.path.join(dir, f"SVE{i}", f"input")
        content = content.replace("{{EXODUS_FILENAME}}", output_base)
        content = content.replace("{{CSV_FILENAME}}", output_base)

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def render_postprocess_block(self, phase, blocks, vars):
        out = ""

        with open(os.path.join(self.FILE_DIR, "volume.i")) as vt:
            volume_temp = vt.read()
        volume_temp = volume_temp.replace("{{PHASE}}", phase)
        volume_temp = volume_temp.replace("{{BLOCKS}}", ' '.join(blocks))
        out += volume_temp + "\n"

        for var in vars:
            with open(os.path.join(self.FILE_DIR, "PostProcess.i")) as t:
                temp = t.read()
            temp = temp.replace("{{PHASE}}", phase)
            temp = temp.replace("{{VAR}}", var)
            temp = temp.replace("{{BLOCKS}}", ' '.join(blocks))
            out += temp + "\n"
        return out

    def write_processing_block(self, dir, i):
        vars = ['gamma_xz', 'gamma_yz', 'tau_xz',
                'tau_yz']

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)

        # Aggregate all blocks per phase
        phase_blocks = {}
        for phase, elem_ids in self.elsets.items():
            for eid in elem_ids:
                etype = self.e_types.get(eid)
                if etype:
                    phase_blocks.setdefault(phase, set()).add(f"{phase}_{etype}")

        with open(out_path, "a") as f:
            f.write("[Postprocessors]\n")
            for phase, blocks in phase_blocks.items():
                block = self.render_postprocess_block(phase, sorted(blocks), vars)
                f.write(block)

        with open(os.path.join(self.FILE_DIR, "PostProcess2.i")) as t, open(out_path, "a") as f:
            f.write(t.read())
            f.write("\n[]\n\n")

    def centroid(self, nodes, nsets):
        pts = {k: nodes[nsets[k][0]] for k in ['bottomleft', 'bottomright', 'topleft', 'topright'] if k in nsets and nsets[k]}
        if len(pts) < 3:
            raise ValueError("Not enough points")
        xs = [pt.x for pt in pts.values()]
        ys = [pt.y for pt in pts.values()]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        lx = abs(pts['bottomright'].x - pts['bottomleft'].x) if 'bottomright' in pts and 'bottomleft' in pts else 1.0
        ly = abs(pts['topleft'].y - pts['bottomleft'].y) if 'topleft' in pts and 'bottomleft' in pts else 1.0
        return (cx, cy)
 
    def write_BcsFunc_block(self, dir, i, centroid, BC):
        if BC == "trac":
            pass
        else:
            x_centroid, y_centroid = centroid

            with open(os.path.join(self.FILE_DIR, f"Func_{BC}_{i}.i")) as f:
                template = f.read()

            # Replace placeholders
            template = template.replace("{{XC}}", str(x_centroid))
            template = template.replace("{{YC}}", str(y_centroid))

            out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
            with open(out_path, "a") as f:
                f.write(template)
                f.write("\n")

    def create_files(self, dir, BC):
        for i in range(3,5):
            sve_path = os.path.join(dir, f"SVE{i}", self.INPUT)
            if os.path.exists(sve_path):
                os.remove(sve_path)  # Clear existing input file to avoid double appending

            self.make_SVE_dir(dir, i)
            self.write_mesh_block(dir, i)
            self.write_var_block(dir, i)
            self.write_kernel_block(dir, i)
            self.write_materials_block(dir, i)
            self.write_auxVar_block(dir, i)
            self.write_auxKer_block(dir, i)
            self.write_BCs_block(dir, i, BC)
            self.write_Exec_block(dir, i, BC)
            self.write_Output_block(dir, i)
            self.write_processing_block(dir, i)
            c = self.centroid(self.ns, self.nsets)
            self.write_BcsFunc_block(dir, i, c, BC)

class OutofPlaneNormalFile:
    EXT = ".inp"    
    FILE_DIR = "ModelFiles/Model_files_OUT_NORM"
    INPUT = 'input.i'

    def __init__(self, nodes, n_map, elements, e_map, e_types, elsets, nsets, BC):
        self.ns = nodes
        self.elms = elements
        self.elsets = elsets
        self.nsets = nsets
        self.e_map = e_map
        self.e_types = e_types
        self.n_map = n_map
        self.BC = BC

    def make_SVE_dir(self, dir, i):
        sve_dir = os.path.join(dir, f"SVE{i}")
        os.makedirs(sve_dir, exist_ok=True)

    def write_mesh_block(self, dir, i):
        mesh_path = os.path.join(dir, "Micro.inp").replace(f"RESULTS_linear", "RESULTS_OOF")
        #mesh_path = os.path.join(dir, "Micro.inp")

        with open(os.path.join(self.FILE_DIR, "MESH.i")) as f:
            content = f.read().replace("{{MESH_FILENAME}}", mesh_path)
        
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "w") as f:
            f.write(content)
            f.write("\n")
    
    def write_var_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Variables.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_params_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "GlobalParams.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def get_phase_type_pairs(self):
        pairs = set()
        for phase, element_ids in self.elsets.items():
            for eid in element_ids:
                etype = self.e_types.get(eid)
                if etype:
                    pairs.add((phase, etype))
        return sorted(pairs)
    
    def _eigs_for_phase(self, nu_val, alpha_L, alpha_T, delta_T, use_real_cte=True):
        if use_real_cte:
            dTtilde = alpha_T + nu_val * alpha_L
        else:
            # Fallback to Poisson's ratio expansion: -nu_LT * [1, 1, 0]^T
            dTtilde = -1.0 * float(nu_val)

        # Format as a space-separated string for MOOSE vector parsing
        e11 = dTtilde * delta_T
        e22 = dTtilde * delta_T
        
        e_vec = f"{e11} {e22} 0 0 0 0"
        return {'e': e_vec}

    def render_material_block(self, phase, elem_type, props):
        with open(os.path.join(self.FILE_DIR, "Materials.i")) as f:
            base = f.read()

        phase_label = f"{phase}_{elem_type}"
        base = (base
                .replace("{{PHASE}}", phase_label)
                .replace("{{ETYPE}}", elem_type)
                .replace("{{BLOCK}}", phase_label))

        if props['model'] == 'iso':
            with open(os.path.join(self.FILE_DIR, "Elasticity_iso.i")) as f:
                elast = f.read()
            elast = (elast
                    .replace("{{PHASE}}", phase_label)
                    .replace("{{BLOCK}}", phase_label)
                    .replace("{{E}}", str(props['E']))
                    .replace("{{NU}}", str(props['nu']))
                    .replace("{{eig}}", str(props['e'])))
        elif props['model'] == 'transverse':
            with open(os.path.join(self.FILE_DIR, "Elasticity_transverse.i")) as f:
                elast = f.read()
            elast = (elast
                    .replace("{{PHASE}}", phase_label)
                    .replace("{{BLOCK}}", phase_label)
                    .replace("{{eig}}", str(props['e'])))
            for key in ['C11', 'C12', 'C13', 'C33', 'C44']:
                elast = elast.replace(f"{{{{{key}}}}}", str(props[key]))
        else:
            raise ValueError(f"Unknown elasticity model: {props['model']}")

        return base.replace("{{ELASTICITY_BLOCK}}", elast)

    def write_materials_block(self, dir_path, i, delta_T):
        import json
        import os

        # Load properties from config
        with open("config.json", "r") as f:
            config = json.load(f)
        
        json_props = config.get("materials", {})

        def iso_C(E, nu):
            return {'model': 'iso', 'E': E, 'nu': nu}

        def transversely_iso_C(E_L, E_T, nu_LT, nu_TT, G_LT):
            delta = E_L/(2*(1-nu_TT)*(E_L/E_T) - 4*nu_LT**2)
            C11 = delta + E_T/(2*(1+nu_TT))
            C12 = delta - E_T/(2*(1+nu_TT))
            C13 = 2*delta*nu_LT
            C33 = E_L + 4*delta*nu_LT**2
            C44 = G_LT
            return {'model': 'transverse', 'C11': C11, 'C12': C12, 'C13': C13, 'C33': C33, 'C44': C44, 'nu_LT': nu_LT}

        # Toggle this boolean to easily switch between Real CTEs and Poisson's ratio
        USE_REAL_CTE = True
        props_map = {}

        for phase, mat in json_props.items():
            # Determine elastic base properties and alphas based on the model
            if mat['model'] == 'iso':
                base_props = iso_C(mat["E"], mat["nu"])
                nu_val = mat["nu"]
                alpha_L = mat.get("alpha", 0.0)
                alpha_T = mat.get("alpha", 0.0)
            elif mat['model'] == 'transverse':
                base_props = transversely_iso_C(mat["E_L"], mat["E_T"], mat["nu_LT"], mat["nu_TT"], mat["G_LT"])
                nu_val = mat["nu_LT"]
                alpha_L = mat.get("alpha_L", 0.0)
                alpha_T = mat.get("alpha_T", 0.0)
            else:
                raise ValueError(f"Unknown model {mat['model']} for phase {phase}")

            # Merge base elastic properties with CTE eigenstrains
            eigs = self._eigs_for_phase(nu_val, alpha_L, alpha_T, delta_T, use_real_cte=USE_REAL_CTE)
            props_map[phase] = {**base_props, **eigs}

        out_path = os.path.join(dir_path, f"SVE{i}", self.INPUT)
        pairs = self.get_phase_type_pairs()

        with open(out_path, "a") as f:
            f.write("[Materials]\n")
            for phase, etype in pairs:
                props = props_map.get(phase)
                if props is None:
                    raise KeyError(f"No props defined for phase '{phase}'")
                block = self.render_material_block(phase, etype, props)
                f.write(block + "\n\n")
            f.write("\n[]\n\n")

    def write_physics_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Physics.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_BC_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, f"{BC}.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")

    def write_Exec_block(self, dir, i, BC):
        with open(os.path.join(self.FILE_DIR, "Exec.i")) as f:
            content = f.read()
        out_path = os.path.join(dir, f'SVE{i}', self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n")
    
    def write_Output_block(self, dir, i):
        with open(os.path.join(self.FILE_DIR, "Outputs.i")) as f:
            content = f.read()

        output_base = os.path.join(dir, f"SVE{i}", f"input")
        content = content.replace("{{EXODUS_FILENAME}}", output_base)
        content = content.replace("{{CSV_FILENAME}}", output_base)

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        with open(out_path, "a") as f:
            f.write(content)
            f.write("\n") 

    def render_postprocess_block(self, phase, blocks, vars):
        out = ""

        with open(os.path.join(self.FILE_DIR, "volume.i")) as vt:
            volume_temp = vt.read()
        volume_temp = volume_temp.replace("{{PHASE}}", phase)
        volume_temp = volume_temp.replace("{{BLOCKS}}", ' '.join(blocks))
        out += volume_temp + "\n"

        for var in vars:
            with open(os.path.join(self.FILE_DIR, "PostProcess.i")) as t:
                temp = t.read()
            temp = temp.replace("{{PHASE}}", phase)
            temp = temp.replace("{{VAR}}", var)
            temp = temp.replace("{{BLOCKS}}", ' '.join(blocks))
            out += temp + "\n"

        label = {
            "grey": "Matrix",
            "white": "Fiber",
            "black": "Inclusion"
        }.get(phase.lower(), phase.capitalize())
        with open(os.path.join(self.FILE_DIR, "PhaseSummary.i")) as ps:
            ps_tmp = ps.read()
        ps_tmp = ps_tmp.replace("{{LABEL}}", label).replace("{{PHASE}}", phase)
        out += ps_tmp + "\n"

        return out

    def write_processing_block(self, dir, i):
        vars = ['strain_xx', 'strain_yy', 'strain_zz', 'strain_yz', 'strain_xz', 'strain_xy', 'stress_xx', 'stress_yy', 'stress_zz', 'stress_yz', 'stress_xz', 'stress_xy']

        out_path = os.path.join(dir, f"SVE{i}", self.INPUT)

        phase_blocks = {}
        for phase, elem_ids in self.elsets.items():
            for eid in elem_ids:
                etype = self.e_types.get(eid)
                if etype:
                    phase_blocks.setdefault(phase, set()).add(f"{phase}_{etype}")

        with open(out_path, "a") as f:
            f.write("[Postprocessors]\n")
            with open(os.path.join(self.FILE_DIR, "Global_volume.i")) as gv:
                f.write(gv.read() + "\n")

            for phase in sorted(phase_blocks.keys()):
                blocks = sorted(phase_blocks[phase])
                block = self.render_postprocess_block(phase, blocks, vars)
                f.write(block)

            with open(os.path.join(self.FILE_DIR, "Globals.i")) as gt:
                gtemp = gt.read()

            vol_block_match = re.search(r"\[\.\/volume_global\][\s\S]*?\[\.{2}\/\]", gtemp)
            if vol_block_match:
                f.write(vol_block_match.group(0) + "\n")

            pervar_template = re.sub(r"\[\.\/volume_global\][\s\S]*?\[\.{2}\/\]\n?", "", gtemp)
            for var in vars:
                f.write(pervar_template.replace("{{VAR}}", var) + "\n")

            with open(os.path.join(self.FILE_DIR, "PhaseSummary.i")) as ps:
                ps_tmp = ps.read()
            f.write(ps_tmp.replace("{{LABEL}}", "Global").replace("{{PHASE}}", "global") + "\n")


            f.write("\n[]\n\n")

    def create_files(self, dir, BC):
        i = 5
        sve_path = os.path.join(dir, f"SVE{i}", self.INPUT)
        if os.path.exists(sve_path):
            os.remove(sve_path) 

        self.make_SVE_dir(dir, i)
        self.write_mesh_block(dir, i)
        self.write_var_block(dir, i)
        self.write_params_block(dir, i)
        self.write_physics_block(dir, i)
        self.write_materials_block(dir, i, delta_T=1) # REAL Del T: -1930)
        self.write_BC_block(dir, i, BC)
        self.write_processing_block(dir, i)
        self.write_Exec_block(dir, i, BC)
        self.write_Output_block(dir, i)