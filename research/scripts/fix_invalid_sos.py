import os
from PIL import Image

def fix_jpeg_sos_parameters(image_folder):
    # Iterate through all files in the directory
    for filename in os.listdir(image_folder):
        # Process only JPEG and PNG files
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            image_path = os.path.join(image_folder, filename)
            try:
                # Open the image
                with Image.open(image_path) as img:
                    # If the image opens without errors, re-save it
                    img.save(image_path, "JPEG")
                    print(f"Re-saved image {filename} successfully to ensure proper SOS parameters.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# Specify your image directory
image_directory = "/ssd1/tuannw/batch4/im"

# Run the function
fix_jpeg_sos_parameters(image_directory)