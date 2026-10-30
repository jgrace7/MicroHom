import numpy as np
import os
import csv
from PIL import Image
from pathlib import Path
from typing import Optional

class InPlaneAnalysis:
    def __init__(self, file_address, filename):
        self.file_address = file_address
        self.filename = filename
        self.stress_matrix = []
        self.strain_matrix = []

        self.stress_matrix_fiber = []
        self.stress_matrix_matrix = []
        self.strain_matrix_fiber = []
        self.strain_matrix_matrix = []

    def get_phase_C_tensor(self, phase_suffix, row):
        C = np.zeros((6, 6))
        idx_map = {
            '11':(0,0), '22':(1,1), '33':(2,2), '44':(3,3), '55':(4,4), '66':(5,5),
            '12':(0,1), '13':(0,2), '23':(1,2), '14':(0,3), '24':(1,3), '34':(2,3),
            '15':(0,4), '25':(1,4), '35':(2,4), '45':(3,4), '46':(3,5), '56':(4,5),
            '16':(0,5), '26':(1,5), '36':(2,5)
        }
        for code, (r, c) in idx_map.items():
            key = f"C{code}_{phase_suffix}"
            if key in row:
                val = float(row[key])
                C[r, c] = val
                C[c, r] = val
        return C

    def read_row(self):
        input_file_name = os.path.join(self.file_address, self.filename)
        try:
            with open(input_file_name, "r") as input_file:
                reader = csv.DictReader(input_file)
                rows = list(reader)
                if not rows:
                    print(f"{input_file_name} is empty.")
                    return (None,) * 8

                last_row = rows[-1]
                try:
                    strain = np.array([
                        float(last_row["avg_strain_xx"]),
                        float(last_row["avg_strain_yy"]),
                        float(last_row["avg_strain_xy"])*2,
                    ])
                    stress = np.array([
                        float(last_row["avg_stress_xx"]),
                        float(last_row["avg_stress_yy"]),
                        float(last_row["avg_stress_xy"]),
                    ])

                    strain_fiber = np.array([
                        float(last_row.get("avg_strain_xx_white", 0.0)),
                        float(last_row.get("avg_strain_yy_white", 0.0)),
                        float(last_row.get("avg_strain_xy_white", 0.0))*2,
                    ])
                    stress_fiber = np.array([
                        float(last_row.get("avg_stress_xx_white", 0.0)),
                        float(last_row.get("avg_stress_yy_white", 0.0)),
                        float(last_row.get("avg_stress_xy_white", 0.0)),
                    ])

                    strain_matrix = np.array([
                        float(last_row.get("avg_strain_xx_grey", 0.0)),
                        float(last_row.get("avg_strain_yy_grey", 0.0)),
                        float(last_row.get("avg_strain_xy_grey", 0.0))*2,
                    ])
                    stress_matrix = np.array([
                        float(last_row.get("avg_stress_xx_grey", 0.0)),
                        float(last_row.get("avg_stress_yy_grey", 0.0)),
                        float(last_row.get("avg_stress_xy_grey", 0.0)),
                    ])

                except ValueError:
                    print(f"NaN present in {input_file_name}.")
                    return (None,) * 8
                
                self.stress_matrix = stress
                self.strain_matrix = strain
                self.stress_matrix_fiber = stress_fiber
                self.strain_matrix_fiber = strain_fiber
                self.stress_matrix_matrix = stress_matrix
                self.strain_matrix_matrix = strain_matrix

                C_fiber = self.get_phase_C_tensor("white", last_row)
                C_matrix = self.get_phase_C_tensor("grey", last_row)
                self.C_matrix_fiber = C_fiber
                self.C_matrix_matrix = C_matrix

                return stress, strain, stress_fiber, strain_fiber, stress_matrix, strain_matrix, C_fiber, C_matrix
            
        except FileNotFoundError:
            print(f"File {input_file_name} does not exist.")
            return (None,) * 8
        except Exception as e:
            print(f"Error reading {input_file_name}: {e}")
            return (None,) * 8

    def form_matrices(self, stresses, strains, stresses_fiber=None, strains_fiber=None,
                    stresses_matrix=None, strains_matrix=None):
        if stresses and strains:
            order = [0, 1, 2]
            stress_values = [stresses[k] for k in order]
            strain_values = [strains[k] for k in order]
            self.stress_matrix = np.transpose(np.array(stress_values))
            self.strain_matrix = np.transpose(np.array(strain_values))

            if stresses_fiber and strains_fiber:
                stress_values_f = [stresses_fiber[k] for k in order]
                strain_values_f = [strains_fiber[k] for k in order]
                self.stress_matrix_fiber = np.transpose(np.array(stress_values_f))
                self.strain_matrix_fiber = np.transpose(np.array(strain_values_f))

            if stresses_matrix and strains_matrix:
                stress_values_m = [stresses_matrix[k] for k in order]
                strain_values_m = [strains_matrix[k] for k in order]
                self.stress_matrix_matrix = np.transpose(np.array(stress_values_m))
                self.strain_matrix_matrix = np.transpose(np.array(strain_values_m))
        else:
            print("No stress or strain.")
            self.stress_matrix = np.array([])
            self.strain_matrix = np.array([])

    def C_matrix(self):
        try:
            inverse_strain = np.linalg.inv(self.strain_matrix)
            C_matrix = self.stress_matrix @ inverse_strain 
        except np.linalg.LinAlgError:
            print("Error: Issue with strain matrix inversion.")
            C_matrix = np.full((3, 3), np.nan)
        return C_matrix


class OutofPlaneAnalysis:
    def __init__(self, file_address, filename):
        self.file_address = file_address
        self.filename = filename
        self.tau_matrix = []
        self.gamma_matrix = []

    def read_row(self):
        input_file_name = os.path.join(self.file_address, self.filename)
        try:
            with open(input_file_name, "r") as input_file:
                reader = csv.DictReader(input_file)
                rows = list(reader)
                
                if not rows:
                    print(f"{input_file_name} is empty")
                    return None, None

                last_row = rows[-1]
                try:
                    gamma = np.array([
                        float(last_row["gamma_xz"]),
                        float(last_row["gamma_yz"])
                    ])
                    tau = np.array([
                        float(last_row["tau_xz"]),
                        float(last_row["tau_yz"])
                    ])
                except ValueError as e:
                    print(f"Nan present in {input_file_name}: {e}")
                    return None, None
                except KeyError as e:
                    print(f"Missing header in {input_file_name}: {e}")
                    return None, None

                return tau, gamma

        except FileNotFoundError:
            print(f"File {input_file_name} does not exist.")
            return None, None
        except Exception as e:
            print(f"Error reading {input_file_name}: {e}")
            return None, None

    def form_matrices(self, taus, gammas):
        if taus and gammas:
            tau_values = [taus[key] for key in sorted(taus)]
            gamma_values = [gammas[key] for key in sorted(gammas)]
            self.tau_matrix = np.transpose(np.array(tau_values))
            self.gamma_matrix = np.transpose(np.array(gamma_values))
        else:
            print("No Stress or Strain.")
            self.tau_matrix = np.array([])
            self.gamma_matrix = np.array([])

    def G_matrix(self):
        try:
            inverse_gamma = np.linalg.inv(self.gamma_matrix)
            G_matrix = self.tau_matrix @ inverse_gamma
        except np.linalg.LinAlgError:
            print("Error: Issue with gamma matrix inversion.")
            G_matrix = np.full((2, 2), np.nan)
        return G_matrix


class Post_Process_Thermal:
    def __init__(self, parent, results_tag, res, img, subimg, LCs, BC, therm_cfg: Optional[dict] = None, inplane_ref: Optional['InPlaneAnalysis'] = None):
        self.parent = Path(parent)
        self.results_tag = results_tag
        self.res = int(res)
        self.img = int(img)
        self.subimg = int(subimg)
        self.BC = str(BC)
        self.cfg = therm_cfg or {}
        self.inplane_ref = inplane_ref

        self.thermal_results_csv = Path(
            self.cfg.get(
                "thermal_results_csv",
                self.parent / f"RESULTS_linear/Res{self.res}x{self.res}/Img{self.img}/SubImg{self.subimg}/SVE5/input.csv"
            )
        )

        self.linear_results_csv = Path(
            self.cfg.get(
                "thermal_results_csv",
                self.parent / f"RESULTS_linear/Res{self.res}x{self.res}/Img{self.img}/SubImg{self.subimg}/SVE0/input.csv"
            )
        )

        self.uniform = bool(self.cfg.get("uniform", True))
        self.delta_T = float(self.cfg.get("delta_T", 1))
        self.output_name = self.cfg.get("output_name", f"MOOSE_FEM_RES{self.res}_{self.BC}.txt")

    @staticmethod
    def _read_last_row(csv_path: Path):
        with open(csv_path, "r", newline="") as f:
            rows = list(csv.DictReader(f))
            if not rows:
                raise FileNotFoundError(f"No rows in {csv_path}")
            return rows[-1]

    def _InPlane_data(self):
        if self.inplane_ref is None:
            raise RuntimeError("No InPlaneAnalysis reference provided")
        inplane = self.inplane_ref
        return (inplane.C_matrix(), inplane.stress_matrix, inplane.strain_matrix,
                inplane.stress_matrix_fiber, inplane.stress_matrix_matrix,
                inplane.strain_matrix_fiber, inplane.strain_matrix_matrix,
                inplane.C_matrix_fiber, inplane.C_matrix_matrix)
        
    def _compute_analytical_2p(self, vf_i, CTT_i, CTT_m, CTT_star, cLT_i, cLT_m, cLL_i, cLL_m, DTT_star):
        """Computes the analytical two-phase concentration and stiffness parameters."""
        if vf_i > 0.0:
            ATT_i_2p = (1/vf_i) * (np.linalg.inv(CTT_i - CTT_m)) @ (CTT_star - CTT_m)
        else:
            ATT_i_2p = np.zeros_like(CTT_m)
            
        ATT_m_2p = (np.eye(3) - vf_i*ATT_i_2p) / (1 - vf_i) if (1 - vf_i) > 0 else np.zeros_like(CTT_m)
        
        cLT_star_2p = vf_i * (ATT_i_2p.T @ cLT_i) + (1 - vf_i) * (ATT_m_2p.T @ cLT_m)
        dLT_star_2p = -DTT_star @ cLT_star_2p
        
        aLT_i_2p = np.linalg.inv(CTT_i - CTT_m) @ (ATT_i_2p - np.eye(3)) @ (cLT_i - cLT_m)
        aLT_m_2p = np.linalg.inv(CTT_m - CTT_i) @ (ATT_m_2p - np.eye(3)) @ (cLT_m - cLT_i)
        aTL_i_2p = aLT_i_2p
        aTL_m_2p = aLT_m_2p
        
        cLL_V = vf_i * cLL_i + (1 - vf_i) * cLL_m
        cLL_star_2p = cLL_V + vf_i * cLT_i @ aTL_i_2p + (1 - vf_i) * cLT_m @ aTL_m_2p
        
        return cLT_star_2p, dLT_star_2p, aTL_i_2p, aTL_m_2p, cLL_star_2p

    def run(self):
        CTT_star, sig, eps, sig_I, sig_M, eps_I, eps_M, C_i, C_m = self._InPlane_data()
        DTT_star = np.linalg.inv(CTT_star)

        trow = self._read_last_row(self.thermal_results_csv)
        lrow = self._read_last_row(self.linear_results_csv)

        sig_therm = np.array([float(trow.get("Global_S11", 0.0)),
                              float(trow.get("Global_S22", 0.0)),
                              float(trow.get("Global_S12", 0.0))])
        
        eps_therm = np.array([float(trow.get("Global_E11", 0.0)),
                              float(trow.get("Global_E22", 0.0)),
                              float(trow.get("Global_E12", 0.0))])
        
        eps_i_therm = np.array([float(trow.get("Fiber_E11", 0.0)),
                                float(trow.get("Fiber_E22", 0.0)),
                                float(trow.get("Fiber_E12", 0.0))])
        
        eps_m_therm = np.array([float(trow.get("Matrix_E11", 0.0)),
                                float(trow.get("Matrix_E22", 0.0)),
                                float(trow.get("Matrix_E12", 0.0))])

        vol_white = float(lrow.get("volume_white", 0.0))
        vol_grey  = float(lrow.get("volume_grey", 0.0))
        vol_black = float(lrow.get("volume_black", 0.0))
        total_vol = vol_white + vol_grey + vol_black

        if total_vol > 0:
            vf_i = vol_white / total_vol
            vf_m = vol_grey / total_vol
            vf_v = vol_black / total_vol
        else:
            vf_i = vf_m = vf_v = 0.0

        dTtheta = (eps_therm - (DTT_star @ sig_therm)) / self.delta_T
        
        alpha_11_star = float(dTtheta[0])
        alpha_22_star = float(dTtheta[1])
        alpha_12_star = float(dTtheta[2])

        in_plane_indices = [0, 1, 5]
        CTT_i = C_i[np.ix_(in_plane_indices, in_plane_indices)]
        CTT_m = C_m[np.ix_(in_plane_indices, in_plane_indices)]

        cLT_i = C_i[in_plane_indices, 2]
        cLT_m = C_m[in_plane_indices, 2]

        ATT_i = eps_I @ np.linalg.inv(eps)
        ATT_m = eps_M @ np.linalg.inv(eps)

        cLT_star = vf_i * (ATT_i.T @ cLT_i) + (1 - vf_i) * (ATT_m.T @ cLT_m)
        dLT_star = -DTT_star @ cLT_star

        aTL_i = (eps_i_therm - (ATT_i @ eps_therm)) / self.delta_T
        aTL_m = (eps_m_therm - (ATT_m @ eps_therm)) / self.delta_T
        aLT_i = aTL_i.T
        aLT_m = aTL_m.T

        cLL_i = C_i[2, 2]
        cLL_m = C_m[2, 2]
        cLL_star = vf_i * (cLL_i + cLT_i @ aTL_i) + (1 - vf_i) * (cLL_m + cLT_m @ aTL_m)

        cLT_star_2p, dLT_star_2p, aTL_i_2p, aTL_m_2p, cLL_star_2p = self._compute_analytical_2p(
            vf_i, CTT_i, CTT_m, CTT_star, cLT_i, cLT_m, cLL_i, cLL_m, DTT_star
        )

        C_star = np.array([cLT_star[0], cLT_star[1], float(cLL_star_2p)])

        return {
            "C11_star": float(C_star[0]),
            "C22_star": float(C_star[1]),
            "C33_star": float(C_star[2]),
            "cLT_star_0": float(cLT_star[0]),
            "dLT_star_0": float(dLT_star[0]),
            "aLT_i_0": float(aTL_i[0]),
            "aLT_m_0": float(aTL_m[0]),
            "cLT_star_0_2p": float(cLT_star_2p[0]),
            "dLT_star_0_2p": float(dLT_star_2p[0]),
            "aLT_i_0_2p": float(aTL_i_2p[0]),
            "aLT_m_0_2p": float(aTL_m_2p[0]),
            "cLL*_2p": float(cLL_star_2p),
            "volume_fraction_inclusion": vf_i,
            "volume_fraction_matrix": vf_m,
            "volume_fraction_void": vf_v,
            "alpha_11_star": alpha_11_star,
            "alpha_22_star": alpha_22_star,
            "alpha_12_star": alpha_12_star,
        }


class Post_Process_Sigma:
    def __init__(self, project_dir, homo_name, res, I, J, LCs, BC, pixel_size_um):
        self.project_dir = project_dir
        self.pixel_size_um = pixel_size_um
        self.homo_name = homo_name
        self.LCs = LCs 
        self.res = res
        self.BC = BC
        self.I = I
        self.J = J

    def get_physical_dimensions(self, i, j, pixel_size_conversion):
        img_path = os.path.join(self.project_dir, "RESULTS_OOF", f"Res{self.res}x{self.res}", f"Img{i}", f"subimage{i}_1.png")
        try:
            with Image.open(img_path) as img:
                width_px, height_px = img.size
                phys_width = width_px * pixel_size_conversion
                phys_height = height_px * pixel_size_conversion
                return phys_width, phys_height
        except FileNotFoundError:
            print(f"Warning: Could not find image to extract size at {img_path}")
            return np.nan, np.nan
        
    def run(self):
        results = []
        results_dir = os.path.join(self.project_dir, self.homo_name, f"Res{self.res}x{self.res}")
        os.makedirs(results_dir, exist_ok=True)

        for i in range(1, self.I + 1):
            img_dir = os.path.join(results_dir, f"Img{i}")

            for j in range(1, self.J + 1):
                sub_dir = os.path.join(img_dir, f"SubImg{j}")
                stresses, strains = {}, {}
                taus, gammas = {}, {}
                stresses_fiber, strains_fiber = {}, {}
                stresses_matrix, strains_matrix = {}, {}

                inplane_ref, shear_analysis = None, None
                C_lin, G = None, None

                for sve_idx in range(self.LCs):
                    sve_dir = os.path.join(sub_dir, f"SVE{sve_idx}")

                    if sve_idx <= 2:
                        rve_analysis = InPlaneAnalysis(sve_dir, "input.csv")
                        stress, strain, stress_fiber, strain_fiber, stress_matrix, strain_matrix, C_fiber, C_matrix = rve_analysis.read_row()
                        if stress is not None and strain is not None:
                            stresses[sve_idx] = stress
                            strains[sve_idx] = strain
                            stresses_fiber[sve_idx] = stress_fiber
                            strains_fiber[sve_idx] = strain_fiber
                            stresses_matrix[sve_idx] = stress_matrix
                            strains_matrix[sve_idx] = strain_matrix
                            inplane_ref = rve_analysis

                    else: 
                        shear_analysis = OutofPlaneAnalysis(sve_dir, "input.csv")
                        tau, gamma = shear_analysis.read_row()
                        if tau is not None and gamma is not None:
                            taus[sve_idx] = tau
                            gammas[sve_idx] = gamma

                if inplane_ref and len(stresses) == 3 and len(strains) == 3:
                    inplane_ref.form_matrices(
                        stresses, strains,
                        stresses_fiber, strains_fiber,
                        stresses_matrix, strains_matrix
                    )
                    C_lin = inplane_ref.C_matrix()

                ppT = Post_Process_Thermal(
                    self.project_dir, self.homo_name,
                    self.res, i, j, self.LCs, self.BC,
                    {}, inplane_ref=inplane_ref
                )
                thermal_results = ppT.run()

                if shear_analysis and taus and gammas:
                    shear_analysis.form_matrices(taus, gammas)
                    G = shear_analysis.G_matrix()

                C_full = np.zeros((6, 6))
                if C_lin is not None and not np.isnan(C_lin).any():
                    C_full[0, 0] = C_lin[0, 0]
                    C_full[1, 1] = C_lin[1, 1]
                    val_12 = 0.5 * (C_lin[0, 1] + C_lin[1, 0])
                    C_full[0, 1] = C_full[1, 0] = val_12
                    C_full[5, 5] = C_lin[2, 2]

                    val_16 = 0.5 * (C_lin[0, 2] + C_lin[2, 0])
                    C_full[0, 5] = C_full[5, 0] = val_16
                    
                    val_26 = 0.5 * (C_lin[1, 2] + C_lin[2, 1])
                    C_full[1, 5] = C_full[5, 1] = val_26

                C_full[0, 2] = C_full[2, 0] = thermal_results["C11_star"] 
                C_full[1, 2] = C_full[2, 1] = thermal_results["C22_star"] 
                C_full[2, 2] = thermal_results["C33_star"]                

                if G is not None and not np.isnan(G).any():
                    C_full[3, 3] = G[1, 1]
                    C_full[4, 4] = G[0, 0]
                    val_45 = 0.5 * (G[0, 1] + G[1, 0])
                    C_full[3, 4] = C_full[4, 3] = val_45

                phys_width, phys_height = self.get_physical_dimensions(i, j, self.pixel_size_um)

                extra_vars = [
                    thermal_results["C33_star"],
                    thermal_results["cLT_star_0"],
                    thermal_results["dLT_star_0"],
                    thermal_results["aLT_i_0"],
                    thermal_results["aLT_m_0"],
                    thermal_results["cLL*_2p"],
                    thermal_results["cLT_star_0_2p"],
                    thermal_results["dLT_star_0_2p"],
                    thermal_results["aLT_i_0_2p"],
                    thermal_results["aLT_m_0_2p"],
                    thermal_results["volume_fraction_inclusion"],
                    thermal_results["volume_fraction_matrix"],
                    thermal_results["volume_fraction_void"],
                    thermal_results["alpha_11_star"],
                    thermal_results["alpha_22_star"],
                    thermal_results["alpha_12_star"],
                    phys_width,
                    phys_height,
                ]

                results.append([i, j] + list(C_full.flatten()) + extra_vars)

        csv_file = os.path.join(results_dir, "Volume_results.csv")
        headers = (
            ["Img", "SubImg"] + 
            [f"C{r+1}{c+1}" for r in range(6) for c in range(6)] + 
            ["cLL_star", "cLT_star", "dLT_star", "aLT_i", "aLT_m", 
             "cLL_star_2p", "cLT_star_2p", "dLT_star_2p", "aLT_i_2p", "aLT_m_2p", 
             "vf_i", "vf_m", "vf_v", "alpha_11_star", "alpha_22_star", "alpha_12_star", 
             "physical_width", "physical_height"]
        )
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(results)

    def assemble(self):
        base_dir = os.path.join(self.project_dir, self.homo_name, f"Res{self.res}x{self.res}")
        results_file = os.path.join(base_dir, "Volume_results.csv")
        out = []
        with open(results_file, "r") as f:
            reader = csv.reader(f)
            next(reader) 

            for row in reader:
                try:
                    img, subimg = int(row[0]), int(row[1])
                    if not (1 <= img <= self.I and 1 <= subimg <= self.J):
                        continue

                    vals = np.array(list(map(float, row[2:38])))
                    C = vals.reshape(6, 6)

                    print(f"Stiffness Matrix (6x6) for res {self.res} Img {img}, SubImg {subimg}:")
                    for row_vals in np.round(C, 6):
                        print(" ".join(f"{val:12.6f}" for val in row_vals))
                    print()

                    out.append((img, subimg, C))
                except Exception as e:
                    print(f"Skipping row due to error: {e}")
                    continue

        return out