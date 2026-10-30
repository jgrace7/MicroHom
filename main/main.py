from __future__ import annotations
import argparse
import logging
import os
import sys
import time
import json
from pathlib import Path
from multiprocessing import Process, Queue
from typing import Iterable, Iterator, List
import subprocess as sub
from PIL import Image
from mean_stiffness_matrix import calculate_mean_stiffness

reconfigure = getattr(sys.stdout, "reconfigure", None)
if reconfigure is not None:
    reconfigure(line_buffering=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def resolve_paths(cfg: dict) -> dict[str, Path]:
    base = Path(__file__).resolve().parent
    grand = base.parent
    sys.path.append(str(base))
    sys.path.append(str(base.parent))
    
    img_dir_path = Path(cfg["img_dir"])
    
    return {
        "parent": grand,
        # "oof2_dir": grand / "oof2_dir" / "OOF2",  # Updated path
        "oof2_prefix": grand / "oof2_dir" / "local_install",
        "moose_sif": grand / "singularity" / "moose.sif", 
        "moose_app": Path(cfg["moose_app"]) if cfg.get("moose_app")
             else grand / "moose" / "modules" / "combined" / "combined-opt",
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
    logging.info("Extracting sub‑images")
    img_ext = "tiff"
    
    for i in range(1, cfg["img"] + 1):
        im_path = paths["img_dir"] / f"{i}.{img_ext}"
        if not im_path.exists():
            continue
            
        with Image.open(im_path) as img:
            dynamic_size = img.width / cfg["res"]
            
        # If binary is True, pass None for threshold2 (edge2)
        edge2 = None if cfg.get("binary") else cfg["edge2"]
            
        ext = ImageExtractor([str(im_path)], dynamic_size, cfg["edge1"], edge2)
        subs, *_ = ext.extract(str(im_path))
        ext.save_subs("RESULTS_OOF", cfg["res"], subs, i - 1, str(im_path), cfg["binary"])

def run_oof2(paths: dict[str, Path], cfg: dict):
    import OOF_Env
    import run_oof2 as oof_runner   # alias: this function is also named run_oof2

    OOF_Env.OOF2Environment.setup_paths()

    base = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    epp = cfg.get("elements_per_pixel", 1.0)
    ps_um = cfg.get("pixel_size_um", 1.0)

    tasks = [(i, j, base, cfg["res"], epp, ps_um)
             for i in range(1, cfg["img"] + 1) for j in range(1, cfg["subimg"] + 1)]

    def worker(i, j, folder, size, elements_per_pixel, pixel_size_um, out_q):
        try:
            result = oof_runner.run(folder, size, i, j, elements_per_pixel, pixel_size_um)
            if result is not True:
                print(f"FAILED Img{i} SubImg{j}: {result}")
            out_q.put((i, j, result))
        except Exception as e:
            print(f"FAILED Img{i} SubImg{j}: {e}")
            out_q.put((i, j, str(e)))

    for chunk in chunked(tasks, cfg["res"]):
        queue = Queue()
        procs = [Process(target=worker, args=(*args, queue)) for args in chunk]
        for p in procs: p.start()
        for p in procs: p.join()

def apply_bcs(paths: dict[str, Path], cfg: dict):
    from SVE_Builder.GenInputs import applyBCs
    base = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    for i in range(1, cfg["img"]+1):
        for j in range(1, cfg["subimg"]+1):
            loc = base / f"Img{i}" / f"SubImg{j}" / "Micro.inp"
            try:
                applyBCs(loc, "RESULTS_linear", "linear", cfg["res"], cfg["BC"], i, j, cfg["materials"])
            except Exception as e:
                logging.error("BC failure %s %s: %s", i, j, e)

def run_sims(paths: dict[str, Path], cfg: dict):
    import shutil
    mpiexec = cfg.get("mpiexec") or shutil.which("mpiexec")
    base = paths["parent"] / "RESULTS_linear" / f"Res{cfg['res']}x{cfg['res']}"
    failures = []
    for i in range(1, cfg["img"] + 1):
        for j in range(1, cfg["subimg"] + 1):
            for k in range(cfg["LCs"]): 
                inp = base / f"Img{i}" / f"SubImg{j}" / f"SVE{k}" / "input.i"
                if not inp.is_file(): continue

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
                    cmd = [
                        mpiexec, "-n", str(cfg["cpus"]), str(paths["moose_app"]), "-i", str(inp)
                    ]

                if cfg["dry"]: continue
                
                logging.info(f"Launching Img{i} SubImg{j} SVE{k}")
                start = time.time()
                proc = sub.Popen(cmd)
                proc.wait()
                elapsed = time.time() - start

                if proc.returncode != 0:
                    logging.error(f"Img{i} SubImg{j} SVE{k} FAILED (exit code {proc.returncode}) after {elapsed:.1f} sec")
                    failures.append((i, j, k))
                    continue
                logging.info(f"Finished in {elapsed:.1f} sec")

    if failures:
        logging.error(f"{len(failures)} simulation(s) failed: {failures}")
        sys.exit(1)

def post_process(paths: dict[str, Path], cfg: dict):
    from PostProcess.postProcess_6LCs import Post_Process_Sigma
    pp = Post_Process_Sigma(
        str(paths["parent"]), "RESULTS_linear", cfg["res"], cfg["img"],
        cfg["subimg"], cfg["LCs"] - 1, cfg["BC"], cfg["pixel_size_um"]
    )
    pp.run()
    pp.assemble()
    results_csv = paths["parent"] / "RESULTS_linear" / f"Res{cfg['res']}x{cfg['res']}" / "Volume_results.csv"
    calculate_mean_stiffness(results_csv)

def run_characterize(paths: dict[str, Path], cfg: dict):
    from subimagecharacterization import characterize_subimages
    subimage_dir = paths["parent"] / "RESULTS_OOF" / f"Res{cfg['res']}x{cfg['res']}"
    char_out_dir = paths["parent"] / "RESULTS_CHAR" / f"Res{cfg['res']}x{cfg['res']}"
    characterize_subimages(subimage_directory=subimage_dir, output_directory=char_out_dir, pixel_size_um=cfg["pixel_size_um"])

def main():
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    cfg = build_config(args)
    paths = resolve_paths(cfg)

    if args.img:   extract_sub_images(paths, cfg)
    if args.oof:   run_oof2(paths, cfg)
    if args.mesh:  apply_bcs(paths, cfg)
    if args.sim:   run_sims(paths, cfg)
    if args.post:  post_process(paths, cfg)
    if args.char: run_characterize(paths, cfg)

if __name__=="__main__":
    main()