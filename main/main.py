from __future__ import annotations
import argparse
import os
import socket
import sys
import time
import traceback
import json
from pathlib import Path
from multiprocessing import Process, Queue
from typing import Iterable, Iterator, List
import subprocess as sub
from PIL import Image
from console_utils import say, fmt_time, tail

reconfigure = getattr(sys.stdout, "reconfigure", None)
if reconfigure is not None:
    reconfigure(line_buffering=True)

# Short names for the load cases (used in the simulation progress messages)
LC_NAMES = {0: "in-plane LC 1", 1: "in-plane LC 2", 2: "in-plane LC 3",
            3: "out-of-plane shear LC 1", 4: "out-of-plane shear LC 2",
            5: "eigenstrain, real CTE"}

def run_step(title, fn, paths, cfg, verbose=False):
    """Run one pipeline step with uniform start / finish / failure messages."""
    say(f"{title} started")
    start = time.time()
    try:
        fn(paths, cfg)
    except Exception as e:
        say(f"{title} FAILED after {fmt_time(time.time() - start)}: {e}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)
    say(f"{title} finished in {fmt_time(time.time() - start)}")

def _resolve(p: str, root: Path) -> Path:
    path = Path(p).expanduser()
    return path if path.is_absolute() else root / path

def resolve_paths(cfg: dict) -> dict[str, Path]:
    base = Path(__file__).resolve().parent
    grand = base.parent
    sys.path.append(str(base))
    sys.path.append(str(base.parent))
    
    img_dir_path = Path(cfg["img_dir"])
    
    return {
        "parent": grand,
        "moose_sif": grand / "singularity" / "moose.sif", 
        "moose_app": _resolve(cfg["moose_app"], grand),
        "img_dir": img_dir_path
    }

def build_config(a: argparse.Namespace) -> dict:
    with open(a.config, 'r') as f:
        json_cfg = json.load(f)
    
    return {
        **vars(a),
        **json_cfg,
        "LCs": 6, 
    }

def parse_arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Homogenization workflow driver")
    p.add_argument("--img", action="store_true")
    p.add_argument("--oof", action="store_true")
    p.add_argument("--mesh", action="store_true")
    p.add_argument("--sim", action="store_true")
    p.add_argument("--post", action="store_true")
    p.add_argument("--char", action="store_true")
    p.add_argument("--config", type=str, default="config.json", help="Path to input JSON")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry", action="store_true")
    return p.parse_args()

def chunked(it: Iterable, n: int) -> Iterator[List]:
    it = iter(it)
    for first in it:
        chunk = [first, *[next(it, None) for _ in range(n-1)]]
        yield [c for c in chunk if c is not None]

def extract_sub_images(paths: dict[str, Path], cfg: dict):
    from ImageExtract import ImageExtractor
    img_ext = "tiff"
    say(f"  {cfg['img']} image(s), {cfg['res']}x{cfg['res']} sub-image grid")

    for i in range(1, cfg["img"] + 1):
        im_path = paths["img_dir"] / f"{i}.{img_ext}"
        if not im_path.exists():
            say(f"  image {i}: {im_path} not found, skipping")
            continue

        with Image.open(im_path) as img:
            dynamic_size = img.width / cfg["res"]

        # If binary is True, pass None for threshold2 (edge2)
        edge2 = None if cfg.get("binary") else cfg["edge2"]

        ext = ImageExtractor([str(im_path)], dynamic_size, cfg["edge1"], edge2)
        subs, *_ = ext.extract(str(im_path))
        ext.save_subs("RESULTS_OOF", cfg["res"], subs, i - 1, str(im_path), cfg["binary"])
        say(f"  image {i}: sub-images extracted")

def run_oof2(paths: dict[str, Path], cfg: dict):
    import contextlib
    import OOF_Env
    import run_oof2 as oof_runner   # alias: this function is also named run_oof2

    OOF_Env.OOF2Environment.setup_paths()

    base = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    epp = cfg.get("elements_per_pixel")
    ps_um = cfg.get("pixel_size_um")

    tasks = [(i, j, base, cfg["res"], epp, ps_um)
             for i in range(1, cfg["img"] + 1) for j in range(1, cfg["subimg"] + 1)]
    say(f"  meshing {len(tasks)} sub-image(s) at {epp} element(s) per pixel")

    def worker(i, j, folder, size, elements_per_pixel, pixel_size_um, out_q):
        start = time.time()
        try:
            # keep OOF2's own start-up chatter off the terminal
            with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn), contextlib.redirect_stderr(dn):
                result = oof_runner.run(folder, size, i, j, elements_per_pixel, pixel_size_um)
        except Exception as e:
            result = str(e)
        mesh_file = Path(folder) / f"Img{i}" / f"SubImg{j}" / "Micro.inp"
        if result is True and mesh_file.is_file():
            say(f"  Img{i} SubImg{j}: meshed in {fmt_time(time.time() - start)}")
            out_q.put((i, j, True))
        else:
            reason = result if result is not True else "no Micro.inp was written"
            say(f"  Img{i} SubImg{j}: FAILED - {reason} (see {Path(folder) / 'oof2_processing.log'})")
            out_q.put((i, j, False))

    failed = []
    for chunk in chunked(tasks, cfg["res"]):
        queue = Queue()
        procs = [Process(target=worker, args=(*args, queue)) for args in chunk]
        for p in procs: p.start()
        for p in procs: p.join()
        for _ in chunk:
            i, j, ok = queue.get()
            if not ok:
                failed.append((i, j))
    if failed:
        raise RuntimeError(f"meshing failed for (Img, SubImg): {failed}")

def apply_bcs(paths: dict[str, Path], cfg: dict):
    from SVE_Builder.GenInputs import applyBCs
    base = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    failures = []
    for i in range(1, cfg["img"]+1):
        for j in range(1, cfg["subimg"]+1):
            loc = base / f"Img{i}" / f"SubImg{j}" / "Micro.inp"
            try:
                applyBCs(loc, "RESULTS_linear", "linear", cfg["res"], cfg["BC"], i, j, cfg["materials"])
                say(f"  Img{i} SubImg{j}: MOOSE inputs written (BC: {cfg['BC']})")
            except Exception as e:
                say(f"  Img{i} SubImg{j}: FAILED - {e}")
                failures.append((i, j))
    if failures:
        raise RuntimeError(f"input generation failed for (Img, SubImg): {failures}")

def run_sims(paths: dict[str, Path], cfg: dict):
    import shutil
    mpiexec = cfg.get("mpiexec") or shutil.which("mpiexec")
    if not cfg.get("cluster"):
        if not paths["moose_app"].is_file():
            raise FileNotFoundError(
                f"MOOSE executable not found: {paths['moose_app']}\n"
                "Build modules/combined (see README) or set 'moose_app' in your config."
            )
        if not mpiexec:
            raise RuntimeError(
                "mpiexec not found. Activate the moose environment or set 'mpiexec' in your config."
            )

    base = paths["parent"] / "RESULTS_linear" / f"Res{cfg['res']}x{cfg['res']}"

    cases = [(i, j, k, base / f"Img{i}" / f"SubImg{j}" / f"SVE{k}" / "input.i")
             for i in range(1, cfg["img"] + 1)
             for j in range(1, cfg["subimg"] + 1)
             for k in range(cfg["LCs"])]
    cases = [c for c in cases if c[3].is_file()]
    if not cases:
        raise FileNotFoundError(f"No MOOSE input files found under {base}. Run --mesh first.")

    mode = "container" if cfg.get("cluster") else "local"
    say(f"  {len(cases)} load case(s) on {socket.gethostname()} with {cfg['cpus']} MPI rank(s), {mode} MOOSE")
    say("  MOOSE output for each case goes to input.log in its SVE folder")

    failures = []
    for n, (i, j, k, inp) in enumerate(cases, 1):
        if cfg.get("cluster"):
            # Execute mpiexec INSIDE the Singularity container
            cmd = [
                "singularity", "exec",
                "--bind", f"{paths['parent']}:{paths['parent']}",
                str(paths["moose_sif"]),
                "mpiexec", "-n", str(cfg["cpus"]),
                cfg.get("moose_exe", "combined-opt"), "-i", str(inp)
            ]
        else:
            # Execute via local MOOSE compilation
            cmd = [mpiexec, "-n", str(cfg["cpus"]), str(paths["moose_app"]), "-i", str(inp)]

        tag = f"[{n}/{len(cases)}] Img{i} SubImg{j} SVE{k} ({LC_NAMES.get(k, 'load case')})"
        if cfg["dry"]:
            say(f"  {tag}: {' '.join(cmd)}")
            continue

        log_path = inp.parent / "input.log"
        say(f"  {tag} running")
        start = time.time()
        with open(log_path, "w") as log:
            proc = sub.Popen(cmd, stdout=log, stderr=sub.STDOUT)
            proc.wait()
        elapsed = time.time() - start

        if proc.returncode != 0:
            say(f"  {tag} FAILED (exit code {proc.returncode}) after {fmt_time(elapsed)}")
            say(f"    last lines of {log_path}:")
            for line in tail(log_path):
                say(f"      {line}")
            failures.append((i, j, k))
        else:
            say(f"  {tag} done in {fmt_time(elapsed)}")

    if failures:
        raise RuntimeError(f"{len(failures)} of {len(cases)} load case(s) failed (Img, SubImg, SVE): {failures}")
    if not cfg["dry"]:
        say(f"  all {len(cases)} load case(s) completed")

def post_process(paths: dict[str, Path], cfg: dict):
    from PostProcess.postProcess_6LCs import Post_Process_Sigma
    pp = Post_Process_Sigma(
        str(paths["parent"]), "RESULTS_linear", cfg["res"], cfg["img"],
        cfg["subimg"], cfg["LCs"] - 1, cfg["BC"], cfg["pixel_size_um"]
    )
    pp.run()
    pp.assemble()
    results_csv = paths["parent"] / "RESULTS_linear" / f"Res{cfg['res']}x{cfg['res']}" / "Volume_results.csv"
    say(f"  stiffness and CTE results written to {results_csv}")

def run_characterize(paths: dict[str, Path], cfg: dict):
    from subimagecharacterization import characterize_subimages
    subimage_dir = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    char_out_dir = paths["parent"] / "RESULTS_CHAR" / f"Res{cfg['res']}x{cfg['res']}"
    characterize_subimages(subimage_directory=subimage_dir, output_directory=char_out_dir, pixel_size_um=cfg["pixel_size_um"])
    say(f"  characterization results written to {char_out_dir}")

def main():
    args = parse_arguments()
    cfg = build_config(args)
    paths = resolve_paths(cfg)

    steps = [
        ("img",  "Image extraction",        extract_sub_images),
        ("oof",  "OOF2 meshing",            run_oof2),
        ("mesh", "MOOSE input generation",  apply_bcs),
        ("sim",  "MOOSE simulation",        run_sims),
        ("post", "Post-processing",         post_process),
        ("char", "Characterization",        run_characterize),
    ]
    selected = [s for s in steps if getattr(args, s[0])]
    if not selected:
        say("No steps selected. Use --img --oof --mesh --sim --post --char.")
        return

    mode = "cluster (containers)" if cfg.get("cluster") else "local"
    say(f"MicroHom started on {socket.gethostname()} | mode: {mode} | config: {args.config}")
    say("Steps: " + ", ".join(title for _, title, _ in selected))
    start = time.time()
    for _, title, fn in selected:
        run_step(title, fn, paths, cfg, args.verbose)
    say(f"All steps finished in {fmt_time(time.time() - start)}")

if __name__=="__main__":
    main()