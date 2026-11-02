"""
Post-processing of the MOOSE results.

Notation follows the write-up "Transverse Isotropy, thermomechanical response":

  Voigt order        (11, 22, 33, 13, 23, 12) -> indices 1..6; engineering shear strains (2*eps_ij)
  T / L / S          transverse (in-plane: 11, 22, 12), longitudinal (out-of-plane: 33),
                     transverse shear (13, 23)
  C*_TT              3x3 in-plane stiffness, C*_TT = <Sigma><E>^-1                     (31)
  D~*_TT             (C*_TT)^-1                                                         (27a)
  c*_TL              [C13, C23, C36]^T = <A_TT^T c_TL>   (c_LT is its transpose)        (26b)
  c*_LL              C33 (= n)                                                          (26d)
  C*_SS              2x2 transverse shear stiffness, ordered [13, 23]
  A^j_TT             strain concentration of phase j, E^j <E>^-1                        (34a)
  a^j_Ttheta         thermal concentration from the thermal LC (LC 4)                   (35a)
  a^j_TL             eps_L concentration (2-phase closed form)                          (32b)
  d~*_Ttheta         adjusted transverse CTE from the thermal LC                        (22a)
  d~*_TL             -D~*_TT c*_TL                                                      (27b)
  E_L*               c*_LT . d~*_TL + c*_LL  (= EL*)                                     (27e)
  c*_Ltheta          <sigma_L>/dtheta from the thermal LC (eps_T=0, eps_L=0)             (18b)
  d~*_Ltheta         c*_LT . d~*_Ttheta + c*_Ltheta                                      (27f)
  d_L*               -d~*_Ltheta / E_L*     (homogenized longitudinal CTE)          (23f)/(27f)
  d_T*               d~*_Ttheta + d_L* * d~*_TL  (homogenized transverse CTE vec)        (23c)
  xi^j               volume fraction of phase j: i = inclusion (white), m = matrix (grey),
                     v = void (black)
  Sigma, E           3x3 matrices whose columns are the volume-averaged stress / strain of
                     LC 1-3 (SVE0-2); LC 4 (thermal, real CTE) is SVE5                  (30)
"""

import numpy as np
import os
import csv
from PIL import Image
from pathlib import Path
from typing import Optional


class InPlaneAnalysis:
    """Transverse (in-plane) load cases LC 1-3: C*_TT and the phase concentrations A^j_TT."""
    def __init__(self, file_address, filename):
        self.file_address = file_address
        self.filename = filename
        self.Sigma_avg = []     # <Sigma>
        self.E_avg = []         # <E>
        self.Sigma_i = []       # Sigma^i (inclusion)
        self.E_i = []
        self.Sigma_m = []       # Sigma^m (matrix)
        self.E_m = []
        self.C_i = np.zeros((6, 6))   # C^i (6x6 phase stiffness, Voigt)
        self.C_m = np.zeros((6, 6))

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
        """Returns <sigma_T>, <eps_T>, sigma_T^i, eps_T^i, sigma_T^m, eps_T^m, C^i, C^m."""
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
                    eps_T = np.array([
                        float(last_row["avg_strain_xx"]),
                        float(last_row["avg_strain_yy"]),
                        float(last_row["avg_strain_xy"])*2,
                    ])
                    sigma_T = np.array([
                        float(last_row["avg_stress_xx"]),
                        float(last_row["avg_stress_yy"]),
                        float(last_row["avg_stress_xy"]),
                    ])

                    eps_T_i = np.array([
                        float(last_row.get("avg_strain_xx_white", 0.0)),
                        float(last_row.get("avg_strain_yy_white", 0.0)),
                        float(last_row.get("avg_strain_xy_white", 0.0))*2,
                    ])
                    sigma_T_i = np.array([
                        float(last_row.get("avg_stress_xx_white", 0.0)),
                        float(last_row.get("avg_stress_yy_white", 0.0)),
                        float(last_row.get("avg_stress_xy_white", 0.0)),
                    ])

                    eps_T_m = np.array([
                        float(last_row.get("avg_strain_xx_grey", 0.0)),
                        float(last_row.get("avg_strain_yy_grey", 0.0)),
                        float(last_row.get("avg_strain_xy_grey", 0.0))*2,
                    ])
                    sigma_T_m = np.array([
                        float(last_row.get("avg_stress_xx_grey", 0.0)),
                        float(last_row.get("avg_stress_yy_grey", 0.0)),
                        float(last_row.get("avg_stress_xy_grey", 0.0)),
                    ])

                except ValueError:
                    print(f"NaN present in {input_file_name}.")
                    return (None,) * 8

                self.Sigma_avg = sigma_T
                self.E_avg = eps_T
                self.Sigma_i = sigma_T_i
                self.E_i = eps_T_i
                self.Sigma_m = sigma_T_m
                self.E_m = eps_T_m

                C_i = self.get_phase_C_tensor("white", last_row)
                C_m = self.get_phase_C_tensor("grey", last_row)
                self.C_i = C_i
                self.C_m = C_m

                return sigma_T, eps_T, sigma_T_i, eps_T_i, sigma_T_m, eps_T_m, C_i, C_m

        except FileNotFoundError:
            print(f"File {input_file_name} does not exist.")
            return (None,) * 8
        except Exception as e:
            print(f"Error reading {input_file_name}: {e}")
            return (None,) * 8

    def form_matrices(self, Sigmas, Es, Sigmas_i=None, Es_i=None, Sigmas_m=None, Es_m=None):
        """Stack the LC 1-3 vectors (dicts keyed by SVE index 0, 1, 2) into the matrices of (30)."""
        if Sigmas and Es:
            order = [0, 1, 2]
            self.Sigma_avg = np.transpose(np.array([Sigmas[k] for k in order]))
            self.E_avg = np.transpose(np.array([Es[k] for k in order]))

            if Sigmas_i and Es_i:
                self.Sigma_i = np.transpose(np.array([Sigmas_i[k] for k in order]))
                self.E_i = np.transpose(np.array([Es_i[k] for k in order]))

            if Sigmas_m and Es_m:
                self.Sigma_m = np.transpose(np.array([Sigmas_m[k] for k in order]))
                self.E_m = np.transpose(np.array([Es_m[k] for k in order]))
        else:
            print("No stress or strain.")
            self.Sigma_avg = np.array([])
            self.E_avg = np.array([])

    def C_TT_star(self):
        """C*_TT = <Sigma> <E>^-1   (31), raw (not symmetrized)."""
        try:
            return self.Sigma_avg @ np.linalg.inv(self.E_avg)
        except np.linalg.LinAlgError:
            print("Error: Issue with strain matrix inversion.")
            return np.full((3, 3), np.nan)


class OutofPlaneAnalysis:
    def __init__(self, file_address, filename):
        self.file_address = file_address
        self.filename = filename
        self.Sigma_S = []
        self.E_S = []

    def read_row(self):
        """Returns sigma_S = [tau_xz, tau_yz] and eps_S = [gamma_xz, gamma_yz] (engineering shear)."""
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
            self.Sigma_S = np.transpose(np.array(tau_values))
            self.E_S = np.transpose(np.array(gamma_values))
        else:
            print("No Stress or Strain.")
            self.Sigma_S = np.array([])
            self.E_S = np.array([])

    def C_SS_star(self):
        """C*_SS = <Sigma_S> <E_S>^-1, ordered [13, 23], raw (not symmetrized)."""
        try:
            inverse_gamma = np.linalg.inv(self.E_S)
            C_SS = self.Sigma_S @ inverse_gamma
        except np.linalg.LinAlgError:
            print("Error: Issue with gamma matrix inversion.")
            C_SS = np.full((2, 2), np.nan)
        return C_SS



class Post_Process_Thermal:
    """Thermal LC 4 (SVE5, real CTE) plus the out-of-plane coupling terms c*_TL, c*_LL."""
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
                "linear_results_csv",
                self.parent / f"RESULTS_linear/Res{self.res}x{self.res}/Img{self.img}/SubImg{self.subimg}/SVE0/input.csv"
            )
        )

        self.uniform = bool(self.cfg.get("uniform", True))
        self.delta_theta = float(self.cfg.get("delta_theta", 1))
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
        ip = self.inplane_ref
        return (ip.C_TT_star(), ip.Sigma_avg, ip.E_avg,
                ip.Sigma_i, ip.Sigma_m, ip.E_i, ip.E_m,
                ip.C_i, ip.C_m)

    @staticmethod
    def _compute_analytical_2p(xi_i, xi_m, C_TT_i, C_TT_m, C_TT_star, c_TL_i, c_TL_m, c_LL_i, c_LL_m, D_tilde_TT_star):
        I3 = np.eye(3)

        if xi_i > 0.0:
            A_TT_i = (1.0 / xi_i) * np.linalg.inv(C_TT_i - C_TT_m) @ (C_TT_star - C_TT_m)
        else:
            A_TT_i = np.zeros_like(C_TT_m)
        A_TT_m = (I3 - xi_i * A_TT_i) / xi_m if xi_m > 0 else np.zeros_like(C_TT_m)

        c_TL_star = xi_i * (A_TT_i.T @ c_TL_i) + xi_m * (A_TT_m.T @ c_TL_m)
        d_tilde_TL_star = -D_tilde_TT_star @ c_TL_star

        a_TL_i = (A_TT_i - I3) @ np.linalg.inv(C_TT_i - C_TT_m) @ (c_TL_i - c_TL_m)
        a_TL_m = -(xi_i / xi_m) * a_TL_i if xi_m > 0 else np.zeros(3)

        c_LL_voigt = xi_i * c_LL_i + xi_m * c_LL_m
        c_LL_star = c_LL_voigt + xi_i * (c_TL_i @ a_TL_i) + xi_m * (c_TL_m @ a_TL_m)

        return c_TL_star, d_tilde_TL_star, a_TL_i, a_TL_m, c_LL_star

    def run(self):
        C_TT_star, Sigma_avg, E_avg, Sigma_i, Sigma_m, E_i, E_m, C_i, C_m = self._InPlane_data()
        D_tilde_TT_star = np.linalg.inv(C_TT_star)

        trow = self._read_last_row(self.thermal_results_csv)
        lrow = self._read_last_row(self.linear_results_csv)

        sigma_T_LC4 = np.array([float(trow.get("Global_S11", 0.0)),
                                float(trow.get("Global_S22", 0.0)),
                                float(trow.get("Global_S12", 0.0))])
        eps_T_LC4 = np.array([float(trow.get("Global_E11", 0.0)),
                              float(trow.get("Global_E22", 0.0)),
                              float(trow.get("Global_E12", 0.0))])
        eps_T_i_LC4 = np.array([float(trow.get("Fiber_E11", 0.0)),
                                float(trow.get("Fiber_E22", 0.0)),
                                float(trow.get("Fiber_E12", 0.0))])
        eps_T_m_LC4 = np.array([float(trow.get("Matrix_E11", 0.0)),
                                float(trow.get("Matrix_E22", 0.0)),
                                float(trow.get("Matrix_E12", 0.0))])

        sigma_L_LC4 = float(trow.get("Global_S33", 0.0))

        vol_white = float(lrow.get("volume_white", 0.0))
        vol_grey = float(lrow.get("volume_grey", 0.0))
        vol_black = float(lrow.get("volume_black", 0.0))
        total_vol = vol_white + vol_grey + vol_black

        if total_vol > 0:
            xi_i = vol_white / total_vol
            xi_m = vol_grey / total_vol
            xi_v = vol_black / total_vol
        else:
            xi_i = xi_m = xi_v = 0.0

        d_tilde_Ttheta_star = (eps_T_LC4 - (D_tilde_TT_star @ sigma_T_LC4)) / self.delta_theta

        T = [0, 1, 5]
        C_TT_i = C_i[np.ix_(T, T)]
        C_TT_m = C_m[np.ix_(T, T)]

        c_TL_i = C_i[T, 2]
        c_TL_m = C_m[T, 2]
        c_LL_i = C_i[2, 2]
        c_LL_m = C_m[2, 2]

        A_TT_i = E_i @ np.linalg.inv(E_avg)
        A_TT_m = E_m @ np.linalg.inv(E_avg)

        c_TL_star = xi_i * (A_TT_i.T @ c_TL_i) + xi_m * (A_TT_m.T @ c_TL_m)
        d_tilde_TL_star = -D_tilde_TT_star @ c_TL_star

        a_Ttheta_i = (eps_T_i_LC4 - (A_TT_i @ eps_T_LC4)) / self.delta_theta
        a_Ttheta_m = (eps_T_m_LC4 - (A_TT_m @ eps_T_LC4)) / self.delta_theta

        c_TL_star_2p, d_tilde_TL_star_2p, a_TL_i_2p, a_TL_m_2p, c_LL_star_2p = self._compute_analytical_2p(
            xi_i, xi_m, C_TT_i, C_TT_m, C_TT_star, c_TL_i, c_TL_m, c_LL_i, c_LL_m, D_tilde_TT_star
        )

        c_LL_star = float(c_LL_star_2p)

        E_L_star = float(c_TL_star @ d_tilde_TL_star + c_LL_star)

        c_Ltheta_star = sigma_L_LC4 / self.delta_theta

        d_tilde_Ltheta_star = float(c_TL_star @ d_tilde_Ttheta_star + c_Ltheta_star)

        d_L_star = -d_tilde_Ltheta_star / E_L_star if E_L_star != 0 else np.nan

        d_T_star = d_tilde_Ttheta_star + d_L_star * d_tilde_TL_star

        return {
            # homogenized out-of-plane coupling (go into the 6x6 matrix)
            "c_TL_star": c_TL_star,                      # [C13, C23, C36]
            "c_LL_star": c_LL_star,                      # C33
            # diagnostics: numeric (from simulations) vs. 2-phase closed form
            "d_tilde_TL_star_11": float(d_tilde_TL_star[0]),
            "a_Ttheta_i_11": float(a_Ttheta_i[0]),
            "a_Ttheta_m_11": float(a_Ttheta_m[0]),
            "c_TL_star_2p_11": float(c_TL_star_2p[0]),
            "d_tilde_TL_star_2p_11": float(d_tilde_TL_star_2p[0]),
            "xi_i": xi_i,
            "xi_m": xi_m,
            "xi_v": xi_v,
            "d_tilde_Ttheta_star": d_tilde_Ttheta_star,  # [11, 22, 12]
            "E_L_star": E_L_star,
            "c_Ltheta_star": c_Ltheta_star,
            "d_tilde_Ltheta_star": d_tilde_Ltheta_star,
            "d_L_star": d_L_star,
            "d_T_star": d_T_star,                        # [11, 22, 12]
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

        T = [0, 1, 5]      # transverse (11, 22, 12) rows/cols of the 6x6 Voigt matrix
        L = 2              # longitudinal (33)
        S = [3, 4]         # transverse shear (13, 23)

        for i in range(1, self.I + 1):
            img_dir = os.path.join(results_dir, f"Img{i}")

            for j in range(1, self.J + 1):
                sub_dir = os.path.join(img_dir, f"SubImg{j}")
                Sigmas, Es = {}, {}                  # <sigma_T>, <eps_T> of LC 1-3
                Sigmas_i, Es_i = {}, {}              # inclusion
                Sigmas_m, Es_m = {}, {}              # matrix
                Sigmas_S, Es_S = {}, {}              # <sigma_S>, <eps_S> of the shear LCs

                inplane_ref, shear_analysis = None, None
                C_TT, C_SS = None, None

                for sve_idx in range(self.LCs):
                    sve_dir = os.path.join(sub_dir, f"SVE{sve_idx}")

                    if sve_idx <= 2:
                        rve_analysis = InPlaneAnalysis(sve_dir, "input.csv")
                        sigma_T, eps_T, sigma_T_i, eps_T_i, sigma_T_m, eps_T_m, C_i, C_m = rve_analysis.read_row()
                        if sigma_T is not None and eps_T is not None:
                            Sigmas[sve_idx] = sigma_T
                            Es[sve_idx] = eps_T
                            Sigmas_i[sve_idx] = sigma_T_i
                            Es_i[sve_idx] = eps_T_i
                            Sigmas_m[sve_idx] = sigma_T_m
                            Es_m[sve_idx] = eps_T_m
                            inplane_ref = rve_analysis

                    else:
                        shear_analysis = OutofPlaneAnalysis(sve_dir, "input.csv")
                        sigma_S, eps_S = shear_analysis.read_row()
                        if sigma_S is not None and eps_S is not None:
                            Sigmas_S[sve_idx] = sigma_S
                            Es_S[sve_idx] = eps_S

                if inplane_ref and len(Sigmas) == 3 and len(Es) == 3:
                    inplane_ref.form_matrices(Sigmas, Es, Sigmas_i, Es_i, Sigmas_m, Es_m)
                    C_TT = inplane_ref.C_TT_star()

                ppT = Post_Process_Thermal(
                    self.project_dir, self.homo_name,
                    self.res, i, j, self.LCs, self.BC,
                    {}, inplane_ref=inplane_ref
                )
                thermal_results = ppT.run()

                if shear_analysis and Sigmas_S and Es_S:
                    shear_analysis.form_matrices(Sigmas_S, Es_S)
                    C_SS = shear_analysis.C_SS_star()

                # Assemble C* in the Voigt order of the write-up: (11, 22, 33, 13, 23, 12).
                # All entries that were measured are written raw (no symmetrization).
                C_full = np.zeros((6, 6))
                if C_TT is not None and not np.isnan(C_TT).any():
                    C_full[np.ix_(T, T)] = C_TT                         # C*_TT

                # c*_TL = [C13, C23, C36]^T was measured (in-plane stress caused by eps_33).
                # The matching row c*_LT is filled from it by major symmetry, since sigma_33 is not measured.
                C_full[T, L] = thermal_results["c_TL_star"]
                C_full[L, T] = thermal_results["c_TL_star"]
                C_full[L, L] = thermal_results["c_LL_star"]             # c*_LL = C33

                if C_SS is not None and not np.isnan(C_SS).any():
                    C_full[np.ix_(S, S)] = C_SS                         # C*_SS, ordered [13, 23]

                phys_width, phys_height = self.get_physical_dimensions(i, j, self.pixel_size_um)

                d_tilde = thermal_results["d_tilde_Ttheta_star"]
                d_T_star = thermal_results["d_T_star"]
                extra_vars = [
                    float(d_tilde[0]),
                    float(d_tilde[1]),
                    float(d_tilde[2]),
                    float(d_T_star[0]),
                    float(d_T_star[1]),
                    float(d_T_star[2]),
                    float(thermal_results["d_L_star"]),
                    thermal_results["xi_i"],
                    thermal_results["xi_m"],
                    thermal_results["xi_v"],
                    phys_width,
                    phys_height,
                ]

                results.append([i, j] + list(C_full.flatten()) + extra_vars)

        csv_file = os.path.join(results_dir, "Volume_results.csv")
        headers = (
            ["Img", "SubImg"] +
            [f"C{r+1}{c+1}" for r in range(6) for c in range(6)] +      # C*_ab, Voigt order 11,22,33,13,23,12
            ["d_tilde_Ttheta_11", "d_tilde_Ttheta_22", "d_tilde_Ttheta_12",
             "d_T_star_11", "d_T_star_22", "d_T_star_12", "d_L_star",
             "xi_i", "xi_m", "xi_v", "physical_width", "physical_height"]
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

                    out.append((img, subimg, C))
                except Exception as e:
                    print(f"Skipping row due to error: {e}")
                    continue

        return out
