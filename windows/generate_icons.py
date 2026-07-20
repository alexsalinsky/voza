"""Generate tray icons and app icon for Voza. Run once: python generate_icons.py"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

def make_icon(filename, bg_color, mic_color, ring_color=None):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=bg_color)
    draw.rounded_rectangle([24, 14, 40, 36], radius=6, fill=mic_color)
    draw.arc([18, 20, 46, 44], start=0, end=180, fill=mic_color, width=3)
    draw.line([32, 44, 32, 50], fill=mic_color, width=3)
    draw.line([24, 50, 40, 50], fill=mic_color, width=3)
    if ring_color:
        draw.ellipse([2, 2, 62, 62], outline=ring_color, width=2)
    img.save(filename, format="ICO", sizes=[(64, 64)])
    print(f"  Created {filename}")


def make_app_icon(filename):
    """Create the main Voza app icon: microphone with a bold V overlay."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- Background: rounded square with gradient feel ---
    # Dark charcoal circle
    draw.rounded_rectangle([8, 8, 248, 248], radius=48, fill=(35, 35, 45, 255))

    # --- Microphone body (centered, upper portion) ---
    mic_color = (180, 180, 190, 255)
    # Mic capsule
    draw.rounded_rectangle([100, 40, 156, 120], radius=28, fill=mic_color)
    # Mic arc (the holder curve)
    draw.arc([76, 60, 180, 155], start=0, end=180, fill=mic_color, width=8)
    # Mic stand
    draw.line([128, 155, 128, 180], fill=mic_color, width=8)
    # Mic base
    draw.line([100, 180, 156, 180], fill=mic_color, width=8)

    # --- Bold "V" overlay in vibrant accent color ---
    v_color = (80, 200, 255, 255)  # Bright electric blue

    # Try to load a bold font, fall back to default
    font = None
    font_size = 130
    # Try common bold font paths
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    # Draw the V centered on the icon
    text = "V"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] + 15  # nudge down slightly

    # Shadow for depth
    draw.text((tx + 3, ty + 3), text, fill=(0, 0, 0, 120), font=font)
    # Main V
    draw.text((tx, ty), text, fill=v_color, font=font)

    # Save as multi-size ICO for crisp display at all sizes
    sizes_to_save = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    imgs = []
    for s in sizes_to_save:
        resized = img.resize(s, Image.LANCZOS)
        imgs.append(resized)

    imgs[0].save(filename, format="ICO", sizes=[s for s in sizes_to_save], append_images=imgs[1:])
    print(f"  Created {filename} (multi-size: {', '.join(str(s[0]) for s in sizes_to_save)})")


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

make_icon("icon_idle.ico", (60, 60, 60, 255), (255, 255, 255, 255))
make_icon("icon_recording.ico", (220, 40, 40, 255), (255, 255, 255, 255), (255, 80, 80, 255))
make_icon("icon_processing.ico", (230, 160, 30, 255), (255, 255, 255, 255))
make_app_icon("voza.ico")
print("  Done!")
