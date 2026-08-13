"""Bản portable nhẹ: chạy Flask cục bộ và mở giao diện bằng trình duyệt mặc định."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import send_from_directory

import file_renamer_gui as tool


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def localize_interface() -> None:
    replacements = {
        '<link rel="preconnect" href="https://fonts.googleapis.com">': "",
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>': "",
        '<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">':
            '<link rel="stylesheet" href="/__portable_assets/brand/brand.css">',
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">':
            '<link rel="stylesheet" href="/__portable_assets/fontawesome/css/all.min.css">',
    }
    for source, target in replacements.items():
        tool.HTML_TEMPLATE = tool.HTML_TEMPLATE.replace(source, target)


def main() -> None:
    localize_interface()
    assets = resource_root() / "assets"
    shared_static = resource_root() / "static"

    if "portable_assets" not in tool.app.view_functions:
        tool.app.add_url_rule(
            "/__portable_assets/<path:filename>", "portable_assets",
            lambda filename: send_from_directory(assets, filename),
        )
    tool.app.view_functions["shared_static"] = lambda filename: send_from_directory(shared_static, filename)
    tool.main()


if __name__ == "__main__":
    main()
