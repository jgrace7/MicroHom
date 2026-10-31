#!/bin/bash
# -------- Resolve paths -----------------------------
SCRIPT_DIR="${SLURM_SUBMIT_DIR:-$(pwd)}"
cd "$SCRIPT_DIR" || { echo "Failed to cd to $SCRIPT_DIR"; exit 1; }
PROJECT_ROOT="$SCRIPT_DIR"
OOF2_SIF="$PROJECT_ROOT/singularity/oof2.sif"

# -------- Set default action flags ------------------
config_file="config.json"
oof="False"; mesh="False"; sim="False"; post="False"; img="False"; char="False"

# -------- Parse CLI args ----------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --img)    img="True"; shift 1 ;;
    --oof)    oof="True"; shift 1 ;;
    --mesh)   mesh="True"; shift 1 ;;
    --sim)    sim="True"; shift 1 ;;
    --post)   post="True"; shift 1 ;;
    --char)   char="True"; shift 1 ;;
    --config) config_file="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# -------- Read cluster flag from config -------------
# Extracts "True" or "False" natively from the JSON
is_cluster=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get('cluster', False))" "$config_file" 2>/dev/null)

# -------- Load modules if available -----------------
if type module &>/dev/null; then
  module load anaconda3/2024.06
  module load openmpi/4.1.5-gcc
fi

# -------- Build command -----------------------------
if [[ "$oof" == "True" ]] && [[ "$is_cluster" == "True" ]]; then
  [[ -f "$OOF2_SIF" ]] || { echo "Missing $OOF2_SIF. Build it first (see README)."; exit 1; }
  cmd=(singularity exec --bind "$PROJECT_ROOT:$PROJECT_ROOT" --pwd "$PROJECT_ROOT" \
        "$OOF2_SIF" python3 "$PROJECT_ROOT/main/main.py" --config "$config_file")
else
  # Run locally without the .sif
  if [ -n "$CONDA_PREFIX" ]; then
    export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
  fi
  cmd=(/usr/bin/python3 "$PROJECT_ROOT/main/main.py" --config "$config_file")
fi

# Append the requested flags to the python command
[[ "$img" == "True"  ]] && cmd+=(--img)
[[ "$oof" == "True"  ]] && cmd+=(--oof)
[[ "$mesh" == "True" ]] && cmd+=(--mesh)
[[ "$sim" == "True"  ]] && cmd+=(--sim)
[[ "$post" == "True" ]] && cmd+=(--post)
[[ "$char" == "True" ]] && cmd+=(--char)

# -------- Run ----------------------------------------
"${cmd[@]}"