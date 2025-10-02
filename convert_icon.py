#!/usr/bin/env python3
"""
Convert PNG to ICO format for PyInstaller
"""

from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    """Convert PNG file to ICO format with multiple sizes"""
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found")
        return False

    try:
        # Open the PNG image
        img = Image.open(png_path)

        # ICO format works best with square images
        # Resize to 256x256 if not already
        if img.size != (256, 256):
            img = img.resize((256, 256), Image.Resampling.LANCZOS)

        # Convert to RGBA if not already (for transparency support)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Save as ICO with multiple sizes for better quality at different scales
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format='ICO', sizes=sizes)

        print(f"Successfully converted {png_path} to {ico_path}")
        return True

    except Exception as e:
        print(f"Error converting image: {e}")
        return False

if __name__ == "__main__":
    png_file = "assets/icon.png"
    ico_file = "assets/icon.ico"

    if convert_png_to_ico(png_file, ico_file):
        print("Icon conversion completed!")
    else:
        print("Icon conversion failed!")
