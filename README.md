# MicroHom: Image-Based Generalized Plane Strain Microstructure Homogenization

MicroHom turns a 2D microstructure image into the full 3D homogenized thermo-elastic
response of the material it represents. Images are segmented into phases, meshed with
[OOF2](https://github.com/usnistgov/OOF2), and analyzed with
[MOOSE](https://mooseframework.inl.gov/) finite elements under generalized plane strain
(GPS) boundary conditions. The output is the apparent 3D stiffness matrix and the effective
coefficients of thermal expansion (CTE). Supported microstructures are two-phase or porous
two-phase materials. Voids are represented by a near-zero-stiffness phase
(see `example/example.json`).

## Method Overview
A 2D image is analyzed with a set of GPS load cases, and the homogenized
3D properties are recovered from a 2D model:

- **In-plane stiffness** comes from the in-plane GPS load cases (displacement, traction, or
  mixed boundary conditions, selected with `BC`).
- **Out-of-plane normal stiffness** for a two-phase or porous two-phase microstructure is computed from a closed-form expression using the results of
  the in-plane cases, so it needs no separate simulation.
- **Out-of-plane shear stiffness** is computed with a surrogate heat-conduction formulation,
  using the analogy between anti-plane shear and steady-state heat conduction.
- **Effective CTE** is computed from an eigenstrain (thermal strain) load case.

Each material phase can be isotropic or transversely isotropic (see `materials` in the
configuration section). Large images can be divided into an n×n grid of sub-images (`res`)
to study statistical volume element (SVE) size effects.

## Architecture & Workflow
The pipeline is organized as independent stages, each selected with a command-line flag (see [Usage](#usage)):
1.  **Image Processing (`--img`):** Thresholds images, differentiates phases, and extracts domain sub-images.
2.  **OOF2 Meshing (`--oof`):** Drives a **stock, unmodified OOF2 install** through its Python API using the scripts in `main/` (`OOF_Env.py`, `run_oof2.py`, `generate_mesh_from_image.py`) to generate uniform quad-meshes from extracted SVEs.
3.  **MOOSE Input File Generation (`--mesh`):** Applies GPS and CTE boundary conditions to the generated meshes.
4.  **MOOSE Simulation (`--sim`):** Executes high-performance finite element analysis using either a containerized or locally compiled MOOSE environment. The `heat_transfer` and `solid_mechanics` modules are required.
5.  **Post-Processing (`--post`):** Assembles stress/strain responses and computes the apparent stiffness and CTE.
6.  **Characterization (`--char`):** Computes sub-image statistics and metrics.

## Project Directory Layout

```
MicroHom/
├── run.sh                          # shell script wrapper
├── config.json                     # your run configuration (see example/example.json)
├── requirements.txt                # Python dependencies
├── main/ 
│   ├── main.py                     # pipeline driver
│   ├── ImageExtract.py             # image extractor and thresholder
│   ├── mean_stiffness_matrix.py    # mean apparent stiffness calculator
│   ├── subimagecharacterization.py # image characterization
│   ├── OOF_Env.py                  # locates the OOF2 install and sets up sys.path
│   ├── run_oof2.py                 # starts OOF2 and calls the mesh generator
│   ├── generate_mesh_from_image.py # meshes images
├── ModelFiles/
│   ├── Model_files_IN/             # MOOSE .i template files for in-plane LCs
│   ├── Model_files_OUT_NORM/       # MOOSE .i template files for out-of-plane normal LC
│   ├── Model_files_OUT_SHEAR/      # MOOSE .i template files for out-of-plane shear LCs
├── SVE_Builder/
│   ├── Elements.py                 # abaqus element dictionary
│   ├── FilerReader.py              # abaqus .inp file reader
│   ├── GenInputs.py                # MOOSE .i file generator
│   ├── Nodes.py                    # node dictionary
│   ├── WriteMooseInput.py          # MOOSE .i file writer
├── PostProcess/
│   ├── postProcess_6LCs.py         # assembles stiffness/CTE results from MOOSE output
├── example/                        # example image and example.json template
├── moose/                          # MOOSE checkout (local mode only; created by you)
├── oof2_dir/                       # OOF2 build (local mode only; created by you)
│   ├── oofcanvas/                  # stock clone
│   ├── OOF2/                       # stock clone
│   └── local_install/              # install prefix for both
└── singularity/                    # .def files and built .sif images
```

## Prerequisites
To run this pipeline, you need the following system-level tools:
*   **[Apptainer/Singularity](https://apptainer.org/):** Required if running MOOSE and OOF2 via containers.
*   **MPI:** For parallel execution of the MOOSE solver. MOOSE installed through conda uses **MPICH**, so the `mpiexec` used for `--sim` must come from the same environment (see [Running the simulation step](#running-the-simulation-step-local-mode)).
*   **Python 3.8+**: For pipeline orchestration.
*   **Local compilation only:** [Conda](https://github.com/conda-forge/miniforge) (for the MOOSE environment), a C++ compiler, and CMake, plus the build dependencies listed in the MOOSE and OOF2 documentation.
*   *Note on GUI:* OOF2 requires `GTK` system libraries if run interactively, though this pipeline relies heavily on automated API calls.

## Base Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jgrace7/MicroHom.git
   cd MicroHom
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Setup: Local vs. Cluster

This pipeline can be run locally (compiling the engines on your host machine) or via Singularity containers (ideal for HPC clusters). This is controlled by the `cluster` flag in `config.json`.

| | `cluster: false` (local) | `cluster: true` (containers) |
|---|---|---|
| **OOF2 (`--oof`)** | `main.py` runs with `/usr/bin/python3` and uses the OOF2 install in `oof2_dir/local_install` | `main.py` runs *inside* `oof2.sif` and uses the OOF2 install baked into the image |
| **MOOSE (`--sim`)** | `mpiexec` with the locally compiled `combined-opt` | `mpiexec` inside `moose.sif`, running `combined-opt` |

The pipeline scripts in `main/` are never copied into OOF2 or the containers. For container runs, `run.sh` binds the whole project directory into the container at the same path, so the same `main/` scripts are used in both modes.

> **Important (cluster mode):** with `cluster: true`, the `--oof` step runs the entire `main.py` inside the OOF2 container. Run `--oof` as its own invocation rather than chaining it with `--sim`, because the simulation step launches the MOOSE container itself and the two should not be nested. Any Python packages imported by `main.py` at startup (e.g. `Pillow`, `numpy`) must also be available inside `oof2.sif`.

### Option A: Containerized Execution (Recommended for Clusters)
If `cluster: true` is set in your config, the pipeline will ignore local installations and execute the MOOSE and OOF2 steps entirely inside isolated Singularity containers.

**Building the Containers:**
We provide Singularity definition files (`.def`) in the `singularity/` directory. Build the `.sif` images using the following commands:
```bash
sudo singularity build singularity/oof2.sif singularity/oof2.def
sudo singularity build singularity/moose.sif singularity/moose.def
```
*(Note: Ensure the resulting `.sif` files remain in the `singularity/` directory, as expected by `main.py` and `run.sh`.)*

`moose.def` builds the **`combined`** MOOSE app (`combined-opt`), which contains `solid_mechanics`, `heat_transfer` and every other MOOSE module. This build is slow and memory-hungry; it uses `make -j 4` by default, so raise that number in the `.def` only if the build machine has plenty of RAM. The MOOSE commit pinned in `moose.def` should match the commit you use for local builds.

**Rebuilding an existing image:** a container build always starts from scratch, so nothing needs to be cleaned first. Rebuild and overwrite the old image with:
```bash
sudo singularity build --force singularity/moose.sif singularity/moose.def
```

The OOF2 container must install OOF2 to `/oof2_dir/local_install`. In container mode, the MOOSE executable name is `combined-opt` unless you set `moose_exe` in `config.json`.

### Option B: Local Compilation
If `cluster: false` is set in your config, you must compile MOOSE and OOF2 directly on your host machine.

**1. Install and Compile MOOSE**
Follow the [official MOOSE Getting Started guide](https://mooseframework.inl.gov/getting_started/) to install Conda and set up the `moose` environment, and clone MOOSE into `MicroHom/moose` (or anywhere you like; see `moose_app` below). Then compile the **combined** app, which includes every MOOSE module:
```bash
conda activate moose
cd /path/to/moose/modules/combined
make -j 4
```

This produces the executable `combined-opt`. By default the pipeline looks for it at `moose/modules/combined/combined-opt` inside the project. If your MOOSE is elsewhere, set `moose_app` in `config.json` to the full path of the executable (see [Configuration](#configuration)).

*Optional: a smaller custom app.* The `combined` app compiles every MOOSE module, which takes time and disk space. MicroHom only needs `solid_mechanics` and `heat_transfer`, so you can instead generate your own MOOSE app with just those two modules (for example with MOOSE's `stork` template; see the MOOSE documentation on creating an application). In the new app's `Makefile`, turn off `ALL_MODULES` and enable only the two modules:
```make
ALL_MODULES      := no
SOLID_MECHANICS  := yes
HEAT_TRANSFER    := yes
```
Build it with `make -j 4` from the `moose` conda environment, then point MicroHom at the resulting executable with `moose_app` (local mode) or `moose_exe` (container mode, after adapting `moose.def` to build your app). Run the example with the custom app to confirm it works before relying on it.

**2. Compile OOF2 and OOFCanvas**
Build **unmodified** OOF2 into `oof2_dir/local_install` (this exact location is required; the pipeline looks for OOF2 there) using native system Python. No files need to be added to or edited in the OOF2 clone. *Ensure your Conda environment is deactivated before running CMake to prevent library conflicts.*
```bash
conda deactivate
mkdir -p oof2_dir && cd oof2_dir

# Build OOFCanvas
git clone https://github.com/usnistgov/oofcanvas.git
cd oofcanvas && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../../local_install -DPython_EXECUTABLE=/usr/bin/python3 -DPython3_EXECUTABLE=/usr/bin/python3
make -j$(nproc) && make install
cd ../..

# Expose pkg-config for OOF2
export PKG_CONFIG_PATH=$(pwd)/local_install/lib/pkgconfig:$(pwd)/local_install/lib64/pkgconfig:$PKG_CONFIG_PATH

# Build OOF2
git clone https://github.com/usnistgov/OOF2.git
cd OOF2 && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../../local_install -DPython_EXECUTABLE=/usr/bin/python3 -DPython3_EXECUTABLE=/usr/bin/python3
make -j$(nproc) && make install
cd ../../..
```

The system Python used here (`/usr/bin/python3`) must be the same one `run.sh` uses to launch the pipeline, since OOF2's compiled modules are tied to that Python version.

**3. Verify the OOF2 install**
From the project root:
```bash
/usr/bin/python3 -c "import sys; sys.path.insert(0,'main'); import OOF_Env; OOF_Env.OOF2Environment.setup_paths(); import oof2; print('ok')"
```
If this prints `ok`, the meshing step can find OOF2.

#### Running the simulation step (local mode)
OOF2 must run with conda **deactivated** (system Python), while MOOSE's `mpiexec` comes from the conda `moose` environment. In local mode, run the pipeline in two stages:

```bash
# Stage 1: image extraction and meshing (conda deactivated)
./run.sh --img --oof --config config.json

# Stage 2: boundary conditions, simulation, post-processing (moose environment active)
conda activate moose
./run.sh --mesh --sim --post --char --config config.json
```

## Configuration
The simulation parameters and execution environments are centrally controlled via `config.json`. Copy `example/example.json` to the project root as a starting point (`cp example/example.json config.json`).

**Key Config Parameters:**
*   `cluster`: Set to `true` to execute via `.sif` containers, or `false` to use local host compilations.
*   `binary`: Set to `true` for black/white images, `false` for multiphase.
*   `elements_per_pixel`: Controls the mesh density in OOF2.
*   `res`: Defines the grid resolution for dividing an image into sub-images (nxn). For example, `res` = 1 makes no divisions, `res` = 2 splits it into a 2x2 grid (4 sub-images).
*   `cpus`: Number of MPI ranks for the MOOSE simulation.
*   `edge1` / `edge2`: Threshold values for image extraction.
*   `img` / `subimg`: Number of SVEs and sub-SVEs to homogenize sequentially.
*   `BC`: Boundary condition type (e.g., `"trac"`, `"mixed"`, `"disp"`).
*   `materials`: Define phase-specific properties (`E`, `nu`, `alpha`, `G`, etc.). For `"model"`, select material symmetry from `"iso"` (isotropic) or `"transverse"` (transversely isotropic).
*   `pixel_size_um`: Physical size of one image pixel in micrometres. **Required**; set it from your image's scale bar. It is used consistently for meshing, post-processing (the physical SVE size) and image characterization.

**Optional MOOSE settings** (omit them to use the defaults):
*   `moose_app`: (local mode) path to the MOOSE executable. Use the full path to `combined-opt` (or your custom app); relative paths are interpreted from the project root. Default: `moose/modules/combined/combined-opt`. `example/example.json` sets this to the default location.
*   `moose_exe`: (cluster mode) name of the executable inside `moose.sif`. Default: `combined-opt`.
*   `mpiexec`: (local mode) path to the MPI launcher used for `--sim`. Default: the first `mpiexec` on your `PATH`. It must come from the same MPI that MOOSE was built with (MPICH for the conda `moose` environment).

Example:
```json
"moose_app": "/home/you/projects/moose/modules/combined/combined-opt"
```

## Quick Start (Example)
1. Copy the example configuration to the project root: `cp example/example.json config.json`.
2. Check `cluster` in `config.json`: `false` if you compiled MOOSE and OOF2 locally, `true` if you built the `.sif` images. If MOOSE is not in `MicroHom/moose`, set `moose_app`.
3. Run the pipeline as described in [Usage](#usage). In local mode this means the two stages from [Running the simulation step](#running-the-simulation-step-local-mode).
4. Inspect the results in `RESULTS_linear/Res1x1/Volume_results.csv`.

## Usage
Use the bash script wrapper (`run.sh`) to execute the pipeline. You can chain multiple steps together in a single command, subject to the environment notes above.

```bash
# Local mode (cluster: false): meshing, then simulation with the moose environment active
./run.sh --img --oof --config config.json
conda activate moose
./run.sh --mesh --sim --post --char --config config.json

# Cluster mode (cluster: true): run the OOF2 step on its own, then the rest
./run.sh --img --oof --config config.json
./run.sh --mesh --sim --post --char --config config.json

# Run only the image extraction and meshing steps with a custom config
./run.sh --img --oof --config custom_config.json
```

## Output
Results are written under the project root. Inside each folder below, results are grouped by grid resolution (`Res<n>x<n>`):

| Folder | Contents |
|---|---|
| `RESULTS_OOF/` | Extracted sub-images, thresholds, and the OOF2 meshes (`Img*/SubImg*/Micro.inp`) |
| `RESULTS_linear/` | MOOSE inputs and outputs for each load case (`Img*/SubImg*/SVE*/`) and the summary file `Volume_results.csv` |
| `RESULTS_CHAR/` | Sub-image characterization statistics (`--char`) |

`Volume_results.csv` has one row per SVE. Its notation follows: **T** = transverse (in-plane: 11, 22, 12), **L** = longitudinal (out-of-plane: 33), **S** = transverse shear (13, 23).

| Columns | Meaning |
|---|---|
| `C11` … `C66` | Apparent stiffness **C\*** (6×6, row-major), Voigt order **(11, 22, 33, 13, 23, 12)** with engineering shear strains. Blocks: **C\*<sub>TT</sub>** = `C11, C12, C16, C22, C26, C66`; **c\*<sub>TL</sub>** = `C13, C23, C36`; **c\*<sub>LL</sub>** = `C33`; **C\*<sub>SS</sub>** = `C44, C45, C55` (ordered 13, 23). Entries that cannot couple for a z-symmetric (monoclinic) material are 0. |
| `dtilde_Ttheta_11`, `_22`, `_12` | Adjusted transverse CTE **d̃\*<sub>Tθ</sub>** from the thermal load case. This is *not* the 3D transverse CTE; see the write-up for the relation. |
| `xi_i`, `xi_m`, `xi_v` | Volume fractions ξ of the inclusion (white), matrix (grey) and void (black). |
| `physical_width`, `physical_height` | Physical size of the SVE (in micrometres, from `pixel_size_um`). |

## Troubleshooting
*   **`Could not find an OOF2 install`:** OOF2 was not installed to `oof2_dir/local_install`. Rebuild it with the commands in Option B, step 2, which install into that directory.
*   **`import oof2` fails or Python-version errors:** OOF2 was built against a different Python than the one launching the pipeline. Rebuild OOF2 with `/usr/bin/python3` (or edit the interpreter in `run.sh`).
*   **Shared-library errors (e.g. OOFCanvas):** add the install's `lib`/`lib64` directory to `LD_LIBRARY_PATH`.
*   **Meshing appears to succeed but no `Micro.inp` is written:** check `oof2_processing.log` in the results directory; errors in the mesh generator are logged there rather than raised.
*   **`'AnisoHeatConduction' is not a registered object`:** the MOOSE executable was built without the `heat_transfer` module (for example from `modules/solid_mechanics` only). Build and use the `combined` app (`combined-opt`), or rebuild `moose.sif` from the current `moose.def`.
*   **`MOOSE executable not found`:** the path in `moose_app` is wrong, or `combined-opt` has not been built. Build `modules/combined` (see Option B) or correct the path in `config.json`.
*   **A simulation case reports `FAILED (exit code ...)`:** the MOOSE run for that load case aborted; the failed cases are listed at the end of `--sim`. Look at the MOOSE error printed above that message.
*   **MPI errors such as `Runtime environment uses unsupported PMI version PMIx` (each case "finishes" in under a second):** the `mpiexec` being used belongs to a different MPI (e.g. OpenMPI) than the one MOOSE was built with (MPICH). Activate the conda `moose` environment before `--sim`, or set `mpiexec` in `config.json`.