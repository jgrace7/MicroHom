import os
from PIL import Image
from datetime import datetime
import contextlib
import sys
import numpy as np

class OOF_Microstructure:
    def __init__(self, work_dir, log_file=None):
        self.work_dir = os.path.abspath(work_dir)
        self.log_file = log_file or os.path.join(self.work_dir, "oof2_processing.log")
        with open(self.log_file, 'w') as f:
            f.write("")

    def log(self, message, fh):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        fh.write(f"{timestamp} {message}\n")
        fh.flush()

    def read_thresholds(self, threshold_file):
        try:
            with open(threshold_file, 'r') as file:
                lines = file.readlines()
                thresholds = [float(line.split(":")[1].strip()) for line in lines]
                
                # Check for either 1 or 2 threshold values instead of just 2
                if len(thresholds) not in [1, 2]:
                    raise ValueError("Threshold file must contain exactly one or two values.")
                return thresholds
        except Exception as e:
            with open(self.log_file, 'a') as log_fh:
                self.log(f"Error reading threshold file: {e}", log_fh)
            return None
        
    def convert_to_plane_strain(self, inp_path):
        with open(inp_path, 'r') as f:
            text = f.read()

        text = text.replace('CPS3', 'CPE3')
        text = text.replace('CPS4', 'CPE4')

        with open(inp_path, 'w') as f:
            f.write(text)

    def Create_From_ImageFile(self, res, I, i, elements_per_pixel=1.0):
        with open(self.log_file, 'a') as log_fh:
            with contextlib.redirect_stdout(log_fh), contextlib.redirect_stderr(log_fh):
                try:
                    from ooflib.SWIG.image import oofimage
                    from ooflib.common import primitives

                    img_name = f"subimage{I}_{i}.png"
                    img_path = os.path.join(self.work_dir, f"Img{I}", img_name)
                    threshold_path = os.path.join(self.work_dir, f"Img{I}", "thresholds.txt")

                    if not os.path.exists(img_path):
                        self.log(f"Error: Image not found at path: {img_path}", log_fh)
                        return

                    thresholds = self.read_thresholds(threshold_path)
                    if thresholds is None:
                        self.log("Error: Could not determine thresholds...", log_fh)
                        return

                    # Unpack 1 or 2 thresholds
                    if len(thresholds) == 1:
                        t1 = thresholds[0]
                        t2 = thresholds[0] # Set t2 = t1 so the grey phase is empty
                    else:
                        t1, t2 = thresholds
                        
                    img = Image.open(img_path).convert('L')
                    pix_val = list(img.getdata())
                    self.log(f"Min pixel value: {min(pix_val)}", log_fh)
                    self.log(f"Max pixel value: {max(pix_val)}", log_fh)


                    width, height = img.size

                    pixel_size_mm = 1/1937 # from scale bar on img
                    #pixel_size_mm = 0.001 # for UD

                    width_physical = width * pixel_size_mm
                    print("width_physical", width_physical, res)
                    height_physical = height * pixel_size_mm
                    dx, dy = width_physical / width, height_physical / height
                    
                    phase_map = {"black": 0, "grey": 1, "white": 2}
                    pixel_groups = {"black": None, "grey": None, "white": None}

                    for ix in range(height):
                        for iy in range(width):
                            global_id = ix * width + iy
                            pixel_val = pix_val[global_id]

                            # The extracted image pixels are strictly 0, 128, and 255.
                            # Use fixed boundaries (64 and 192) to reliably group them.
                            if pixel_val < 64 and pixel_groups["black"] is None:
                                pixel_groups["black"] = (ix, iy)
                            elif 64 <= pixel_val < 192 and pixel_groups["grey"] is None:
                                pixel_groups["grey"] = (ix, iy)
                            elif pixel_val >= 192 and pixel_groups["white"] is None:
                                pixel_groups["white"] = (ix, iy)

                            if all(v is not None for v in pixel_groups.values()):
                                break
                        if all(v is not None for v in pixel_groups.values()):
                            break

                    OOF.Microstructure.Create_From_ImageFile(
                        filename=img_path,
                        microstructure_name="micro",
                        height=height_physical, width=width_physical
                    )
                    OOF.Windows.Graphics.New()
                    OOF.Graphics_1.Settings.New_Layer_Policy(policy='Always')
                    OOF.Graphics_1.Layer.New(category='Image', what='micro:' + img_name, how=BitmapDisplayMethod())

                    for phase, coords in pixel_groups.items():
                        if coords is None:
                            self.log(f"Warning: No pixels found for {phase} phase in image {img_name}", log_fh)
                            continue

                        ix, iy = coords
                        coordx = float(iy) * dx + 0.5 * dx
                        coordy = height_physical - (float(ix) * dy + 0.5 * dy)
                        OOF.Graphics_1.Toolbox.Pixel_Select.Color(
                            source='micro:' + img_name,
                            range=DeltaGray(delta_gray=0.25),
                            points=[Point(coordx, coordy)], shift=False, ctrl=False
                        )
                        OOF.PixelGroup.New(name=phase, microstructure='micro')
                        OOF.PixelGroup.AddSelection(microstructure='micro', group=phase)
                        self.log(f"Selected {phase} phase at ({ix}, {iy})", log_fh)

                    for phase in phase_map.keys():
                        if pixel_groups[phase] is not None:
                            OOF.Material.New(name=phase, material_type='bulk')
                            OOF.Material.Add_property(name=phase, property='Mechanical:Elasticity:Isotropic')
                            OOF.Material.Assign(material=phase, microstructure='micro', pixels=phase)
                        else:
                            self.log(f"Skipping material assignment for {phase} (no pixels found)", log_fh)

                    #l_ch = 0.0017746913580246912 # from calculation
                    E = 4.13 # Young's modulus (GPa), use E_T for transverse isotropic materials.
                    f_t = 65.2 # Tensile strength (MPa)
                    G_f = 0.18 # Fracture energy (kJ/m^2), also presented as G_c (critical energy release rate)
                    l_ch = ((E*G_f)/f_t**2)*1000 # Irwin characteristic length (mm)
                    b = (2/np.pi)*l_ch # regularization length scale for linear softening law (a1 = 2 from Wu 2017)
                    # characteristic length h/3, h/5
                    h_max = b/3 # max mesh refinement
                    h_min = b/5 # min mesh refinement


                    print('min and max sacle', h_min, h_max)

                    x_els = max(1, int(round(width * elements_per_pixel)))
                    y_els = max(1, int(round(height * elements_per_pixel)))
                    
                    self.log(f"Meshing: {width}x{height} pixels at {elements_per_pixel} els/pix -> {x_els}x{y_els} elements", log_fh)

                    # USE THIS FOR REAL STUFF
                    #OOF.Skeleton.Auto(
                    #    name='microskeleton',
                    #    microstructure='micro',
                    #    left_right_periodicity=True,
                    #    top_bottom_periodicity=True,
                    #    maxscale=h_max,
                    #    minscale=h_min,
                    #    units='Physical',
                    #    threshold=.9
                    #)

                    OOF.Skeleton.New(
                        name='microskeleton',
                        microstructure='micro',
                        x_elements=x_els,
                        y_elements=y_els,
                        skeleton_geometry=QuadSkeleton(
                            left_right_periodicity=True,
                            top_bottom_periodicity=True
                        )
                    )

                    # control element types
                    #OOF.Mesh.New(name='microv1', skeleton='micro:microskeleton', element_types=['D2_2', 'T3_3', 'Q4_4'])
                    OOF.Mesh.New(name='microv1', skeleton='micro:microskeleton', element_types=['Q4_4'])

                    output_dir = os.path.join(self.work_dir, f'Img{I}', f'SubImg{i}')
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, 'Micro.inp')
                    OOF.File.Save.Mesh(filename=output_path, mode='w', format='abaqus', mesh='micro:microskeleton:microv1')
                    self.log(f"Mesh saved to {output_path}", log_fh)

                    self.convert_to_plane_strain(output_path)

                    # Cleanup
                    OOF.Mesh.Delete(mesh='micro:microskeleton:microv1')
                    for phase in phase_map.keys():
                        if pixel_groups[phase] is not None:
                            OOF.Material.Delete(name=phase)
                    OOF.Skeleton.Delete(skeleton='micro:microskeleton')
                    OOF.Microstructure.Delete(microstructure="micro")
                    self.log("Cleanup completed.", log_fh)



                except Exception as e:
                    self.log(f"Error during processing: {e}", log_fh)
