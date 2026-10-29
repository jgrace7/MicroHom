import os
from PIL import Image
import numpy as np

class Thresholding:
    def __init__(self, image_path, phase_values, threshold1, threshold2=None, binary=False):
        self.image_path = image_path
        self.threshold1 = threshold1
        # When binary is True, we ignore threshold2.
        self.threshold2 = threshold2 if threshold2 is not None else threshold1
        self.binary = binary
        self.phase_values = phase_values

    def apply_thresholding(self):
        image = Image.open(self.image_path).convert('L')
        image_array = np.array(image)

        if self.binary:
            # Binary logic: below edge1 (threshold1) -> 128 (grey), else -> 255 (white)
            segmented_image = np.where(image_array < self.threshold1, 128, 255)
            unique_vals = np.unique(segmented_image)
            print("Unique pixel values:", unique_vals)
            return Image.fromarray(segmented_image.astype(np.uint8)), (self.threshold1,)
        else:
            # 3-phase logic
            phase1, phase2, phase3 = self.phase_values
            segmented_image = np.where(image_array < self.threshold1, phase1, 
                               np.where(image_array < self.threshold2, phase2, phase3))
            return Image.fromarray(segmented_image.astype(np.uint8)), (self.threshold1, self.threshold2)

    def save_thresholded_image(self, output_path):
        processed_image, thresholds = self.apply_thresholding()
        processed_image.save(output_path)
        return thresholds

class ImageExtractor:
    def __init__(self, original_image_paths, sub_image_size, threshold1, threshold2=None, step_size=None, phase_values=(0, 128, 255)):
        self.original_image_paths = original_image_paths  
        self.sub_image_size = int(sub_image_size)
        self.threshold1 = threshold1
        self.threshold2 = threshold2
        self.phase_values = phase_values
        self.step_size = step_size if step_size else sub_image_size  
        print(f"Sub-image size: {self.sub_image_size}, Step size: {self.step_size}")

    def extract(self, image_path):
        original_image = Image.open(image_path)
        original_array = np.array(original_image)
        height, width = original_array.shape[:2]

        stride = self.sub_image_size
        sub_images = []

        for i in range(0, height - self.sub_image_size + 1, stride): 
            for j in range(0, width - self.sub_image_size + 1, stride):
                sub_image = original_array[i:i + self.sub_image_size, j:j + self.sub_image_size]
                sub_images.append(sub_image)

        num_sub_images_x = height // stride
        num_sub_images_y = width // stride

        return sub_images, num_sub_images_x, num_sub_images_y

    def save_subs(self, output_directory, res, sub_images, img_idx, image_path, binary):
        res_dir = os.path.join(output_directory, f"Res{res}x{res}")
        os.makedirs(res_dir, exist_ok=True)

        img_dir = os.path.join(res_dir, f"Img{img_idx + 1}")  
        os.makedirs(img_dir, exist_ok=True)

        # Pass the binary flag to Thresholding so the correct logic applies
        thresholding = Thresholding(image_path, self.phase_values, self.threshold1, self.threshold2, binary=binary) 
        _, thresholds = thresholding.apply_thresholding()

        # Write out either 1 or 2 thresholds based on the binary flag
        with open(os.path.join(img_dir, "thresholds.txt"), "w") as file:
            file.write(f"Threshold1: {thresholds[0]}\n")
            if not binary:
                file.write(f"Threshold2: {thresholds[1]}\n")

        # Apply the same logic directly to each extracted sub-image array
        for sub_idx, sub_image in enumerate(sub_images):
            sub_image_pil = Image.fromarray(sub_image).convert('L')
            arr = np.array(sub_image_pil)

            if binary:
                # Same binary logic: below edge1 (threshold1) -> 128 (grey), else -> 255 (white)
                thresholded_array = np.where(arr < self.threshold1, 128, 255)
            else:
                phase1, phase2, phase3 = self.phase_values
                thresholded_array = np.where(arr < self.threshold1, phase1,
                                    np.where(arr < self.threshold2, phase2, phase3))

            thresholded_pil = Image.fromarray(thresholded_array.astype(np.uint8))
            
            filename = f"subimage{img_idx + 1}_{sub_idx + 1}.png"
            filepath = os.path.join(img_dir, filename)
            thresholded_pil.save(filepath)

        print(f"Thresholded sub-images saved in: {img_dir}")