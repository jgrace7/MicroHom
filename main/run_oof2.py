import sys, os, copy
import OOF_Env

def run_modules(work_dir, res, I, i, elements_per_pixel, pixel_size_um, oofglobals):
    import generate_mesh_from_image as test_module
    test_module.__dict__.update(oofglobals)
    try:
        micro = test_module.OOF_Microstructure(work_dir)
        micro.Create_From_ImageFile(res, I, i, elements_per_pixel, pixel_size_um)
        return True
    except Exception as e:
        return str(e)

def run(work_dir, res, I, i, elements_per_pixel=1.0, pixel_size_um=1.0):
    OOF_Env.OOF2Environment.setup_paths()
    import oof2
    from ooflib.common import oof
    sys.argv = [sys.argv[0], "--text", "--quiet", "--seed=17"]
    oof.run(no_interp=1)
    from ooflib.common import utils
    oofglobals = copy.copy(utils.OOFglobals())
    return run_modules(work_dir, res, I, i, elements_per_pixel, pixel_size_um, oofglobals)