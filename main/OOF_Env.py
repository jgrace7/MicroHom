import glob
import os
import sys


class OOF2Environment:
    @staticmethod
    def find_prefix():
        """Locate the OOF2 install prefix (the dir containing lib/pythonX.Y/...)."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.environ.get("OOF2_PREFIX"),                            # explicit override
            os.path.join(project_root, "oof2_dir", "local_install"),  # local build
            "/oof2_dir/local_install",                                # inside oof2.sif (adjust to your .def)
        ]
        for c in candidates:
            if c and os.path.isdir(c):
                return c
        raise RuntimeError(
            "Could not find an OOF2 install. Build it into oof2_dir/local_install "
            "(see README) or set OOF2_PREFIX."
        )

    @staticmethod
    def setup_paths():
        prefix = OOF2Environment.find_prefix()
        py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"

        site_dirs = []
        for lib in ("lib", "lib64"):
            site_dirs += glob.glob(os.path.join(prefix, lib, py_ver, "*-packages"))

        for sp in site_dirs:
            for path in (sp, os.path.join(sp, "oof2"), os.path.join(sp, "oof2", "ooflib")):
                if path not in sys.path and os.path.exists(path):
                    sys.path.append(path)