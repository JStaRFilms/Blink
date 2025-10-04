from PIL import Image
import os

def convert_png_to_bmp(png_path, bmp_path):
    """Convert PNG to BMP format."""
    try:
        with Image.open(png_path) as img:
            # Convert to RGB if necessary (BMP doesn't support transparency well)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(bmp_path, 'BMP')
            print(f"Converted {png_path} to {bmp_path}")
    except Exception as e:
        print(f"Error converting {png_path}: {e}")

if __name__ == "__main__":
    assets_dir = "assets"

    # Convert installer banner
    banner_png = os.path.join(assets_dir, "installer_banner.png")
    banner_bmp = os.path.join(assets_dir, "installer_banner.bmp")
    convert_png_to_bmp(banner_png, banner_bmp)

    # Convert wizard icon
    icon_png = os.path.join(assets_dir, "wizard_icon.png")
    icon_bmp = os.path.join(assets_dir, "wizard_icon.bmp")
    convert_png_to_bmp(icon_png, icon_bmp)
