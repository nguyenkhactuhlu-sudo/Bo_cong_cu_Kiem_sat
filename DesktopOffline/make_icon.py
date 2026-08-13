"""Tạo icon Windows nhiều kích thước từ logo chính của dự án."""

from pathlib import Path

from PIL import Image


root = Path(__file__).resolve().parents[1]
source = root / "static" / "logo_moi.png"
target = Path(__file__).resolve().parent / "vendor" / "app.ico"

with Image.open(source) as image:
    image.load()
    if image.width < 64 or image.height < 64:
        raise SystemExit(f"Logo quá nhỏ để tạo icon: {image.size}")
    rgba = image.convert("RGBA")
    target.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(target, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print(f"Icon sẵn sàng: {target}")
