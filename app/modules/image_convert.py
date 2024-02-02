import io
import os
from PIL import Image


def resize_and_crop_image(image, target_width, target_height):
    # Calculate aspect ratio of desired crop
    target_ratio = target_width / target_height
    original_width, original_height = image.size
    original_ratio = original_width / original_height

    if original_width == target_width and original_height == target_height:
        return image

    # Determine if the image needs to be resized based on its aspect ratio
    if original_ratio > target_ratio:
        # Image is wider than needed, resize based on height
        new_height = target_height
        new_width = int(target_height * original_ratio)
    else:
        # Image is taller than needed, resize based on width
        new_width = target_width
        new_height = int(target_width / original_ratio)

    # Resize the image to ensure the crop will cover the target dimensions
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    # Calculate crop area
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = (new_width + target_width) / 2
    bottom = (new_height + target_height) / 2

    # Crop the image
    cropped_image = resized_image.crop((left, top, right, bottom))
    return cropped_image


def process_images(image_data, id, name):
    # Define the target dimensions
    target_dimensions = [(640, 360), (320, 180)]

    # Open the image from image data
    with Image.open(io.BytesIO(image_data)) as img:
        for width, height in target_dimensions:
            # Resize and crop the image
            processed_img = resize_and_crop_image(img, width, height)

            # Convert to WebP and save
            new_folder = f"thumbnails_{name}_{width}px"
            new_file_name = f"{id}.webp"
            os.makedirs(new_folder, exist_ok=True)
            processed_img.save(os.path.join(new_folder, new_file_name), "WEBP")
