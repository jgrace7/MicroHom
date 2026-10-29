# MicroHom: Image-Based Generalized Plane Strain Microstructure Homogenization

An automated computational pipeline for extracting Statistical Volume Elements (SVEs) from microstructure imagery, generating finite element meshes, and performing thermo-mechanical homogenization.

This workflow utilizes Generalized Plane Strain (GPS) boundary conditions to compute apparent elastic properties and Coefficient of Thermal Expansion (CTE) from two-phase or multiphase microstructures.

## Architecture & Workflow
The pipeline operates through modular, concurrent execution of the following stages:
1.  **Image Processing (`--img`):** Extracts domain sub-images, quantizes phases, and characterizes morphology using `scikit-image` and `Pillow`.
2.  **Meshing (`--oof`):** Drives a **stock, unmodified OOF2 install** through its Python API using the scripts in `main/` (`OOF_Env.py`, `run_oof2.py`, `generate_mesh_from_image.py`) to generate representative quad-meshes from extracted SVEs.
3.  **Boundary Conditions (`--mesh`):** Applies GPS and CTE boundary conditions to the generated meshes.
4.  **Simulation (`--sim`):** Executes high-performance finite element analysis using either a containerized or locally compiled MOOSE environment.
5.  **Post-Processing (`--post`):** Assembles stress/strain responses and calculates mean stiffness matrices.
6.  **Characterization (`--char`):** Computes sub-image statistics and metrics.

## Project Layout
All custom code lives in `main/`. OOF2 is used as-is: you never need to copy or edit files inside the OOF2 source tree.

```
MicroHom/
├── run.sh                         # entry point
├── config.json                    # your run configuration (see example.json)
├── main/
│   ├── main.py                    # pipeline driver
│   ├── OOF_Env.py                 # locates the OOF2 install and sets up sys.path
│   ├── run_oof2.py                # starts OOF2 and calls the mesh generator
│   ├── generate_mesh_from_image.py
│   └── ...                        # SVE_Builder, PostProcess, ImageExtract, etc.
├── oof2_dir/                      # created by you (Option B only)
│   ├── oofcanvas/                 # stock clone
│   ├── OOF2/                      # stock clone
│   └── local_install/             # install prefix for both
└── singularity/                   # .def files and built .sif images
```

## Prerequisites
To run this pipeline, you need the following system-level tools:
*   **[Apptainer/Singularity](https://apptainer.org/):** Required if running MOOSE and OOF2 via containers.
*   **MPI (OpenMPI/MPICH):** For parallel execution of the MOOSE solver.
*   **Python 3.8+**: For pipeline orchestration.
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
| **MOOSE (`--sim`)** | `mpiexec` with the locally compiled `solid_mechanics-opt` | `mpiexec` inside `moose.sif` |

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

The OOF2 container must install OOF2 to `/oof2_dir/local_install`. If your image uses a different prefix, set `OOF2_PREFIX` to that location (for example, by adding `--env OOF2_PREFIX=/your/prefix` to the `singularity exec` line in `run.sh`).

### Option B: Local Compilation
If `cluster: false` is set in your config, you must compile MOOSE and OOF2 directly on your host machine.

**1. Install and Compile MOOSE**
Follow the [official MOOSE Getting Started guide](https://mooseframework.inl.gov/getting_started/) to install Conda and set up the `moose` environment. Then, compile the solid mechanics module:
```bash
conda activate moose
cd /path/to/moose/modules/solid_mechanics
make -j 4
```

**2. Compile OOF2 and OOFCanvas**
Build **unmodified** OOF2 into `oof2_dir/local_install` using native system Python. No files need to be added to or edited in the OOF2 clone. *Ensure your Conda environment is deactivated before running CMake to prevent library conflicts.*
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

**3. (Optional) Install OOF2 elsewhere**
`main/OOF_Env.py` looks for the OOF2 install prefix in this order:
1. The `OOF2_PREFIX` environment variable
2. `oof2_dir/local_install` inside this repository
3. `/oof2_dir/local_install` (the container location)

If you installed OOF2 somewhere else, export the prefix before running:
```bash
export OOF2_PREFIX=/path/to/your/oof2/install
```

**4. Verify the OOF2 install**
From the project root:
```bash
/usr/bin/python3 -c "import sys; sys.path.insert(0,'main'); import OOF_Env; OOF_Env.OOF2Environment.setup_paths(); import oof2; print('ok')"
```
If this prints `ok`, the meshing step can find OOF2.

## Configuration
The simulation parameters and execution environments are centrally controlled via `config.json` (see `example.json` for a template).

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

## Usage
Use the bash script wrapper (`run.sh`) to execute the pipeline. You can chain multiple steps together in a single command.

```bash
# Run the entire pipeline sequentially (local mode, cluster: false)
./run.sh --img --oof --mesh --sim --post --char

# Run only the image extraction and meshing steps with a custom config
./run.sh --img --oof --config custom_config.json

# Cluster mode (cluster: true): run the OOF2 step on its own, then the rest
./run.sh --img --oof
./run.sh --mesh --sim --post --char
```

## Troubleshooting
*   **`Could not find an OOF2 install`:** OOF2 was not installed to `oof2_dir/local_install`. Rebuild with the install prefix above or set `OOF2_PREFIX`.
*   **`import oof2` fails or Python-version errors:** OOF2 was built against a different Python than the one launching the pipeline. Rebuild OOF2 with `/usr/bin/python3` (or edit the interpreter in `run.sh`).
*   **Shared-library errors (e.g. OOFCanvas):** add the install's `lib`/`lib64` directory to `LD_LIBRARY_PATH`.
*   **Meshing appears to succeed but no `Micro.inp` is written:** check `oof2_processing.log` in the results directory; errors in the mesh generator are logged there rather than raised.