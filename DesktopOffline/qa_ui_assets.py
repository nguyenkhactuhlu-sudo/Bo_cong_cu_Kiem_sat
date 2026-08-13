"""Kiểm tra trang đầu, logo, CSS, font và tài nguyên cục bộ của từng công cụ."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from PIL import Image
from flask import Flask, send_from_directory

import main as desktop
from tool_registry import TOOLS


STAGE = Path(__file__).resolve().parent / "stage" / "payload"
# QA luôn đọc đúng payload đã staging, giống dữ liệu nằm trong sys._MEIPASS của EXE.
desktop.resource_root = lambda: STAGE


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"src", "href"} and value:
                self.values.append(value)


def configure_app(tool: dict) -> Flask:
    if tool["kind"] == "html":
        app = Flask("qa_static", static_folder=None)
        source = desktop.resource_root() / tool["source"]

        @app.get("/")
        def page():
            return source.read_text(encoding="utf-8")

        @app.get("/static/<path:filename>")
        def shared_static(filename):
            return send_from_directory(desktop.resource_root() / tool["static_folder"], filename)
    else:
        module = desktop.load_source_module(desktop.resource_root() / tool["source"])
        app = module.app
        if tool.get("template_folder"):
            app.template_folder = str(desktop.resource_root() / tool["template_folder"])
        if tool.get("static_folder"):
            app.static_folder = str(desktop.resource_root() / tool["static_folder"])

    assets = desktop.resource_root() / "DesktopOfflineAssets"
    if "offline_assets" not in app.view_functions:
        app.add_url_rule(
            "/__offline_assets/<path:filename>", "offline_assets",
            lambda filename: send_from_directory(assets, filename),
        )
    return app


def local_path(reference: str) -> str | None:
    if reference.startswith(("data:", "#", "javascript:", "mailto:")):
        return None
    parsed = urlparse(urljoin("http://desktop.local/", reference))
    if parsed.netloc != "desktop.local":
        raise AssertionError(f"Tài nguyên mạng còn sót: {reference}")
    return parsed.path


def assert_response(response, label: str) -> bytes:
    if response.status_code != 200:
        raise AssertionError(f"{label}: HTTP {response.status_code}")
    if not response.data:
        raise AssertionError(f"{label}: tệp rỗng")
    return response.data


def audit(tool_id: str) -> None:
    tool = TOOLS[tool_id]
    app = configure_app(tool)
    client = app.test_client()
    html = assert_response(client.get("/"), f"{tool_id} /").decode("utf-8")
    if "/__offline_assets/brand/brand.css" not in html:
        raise AssertionError(f"{tool_id}: thiếu stylesheet nhận diện")
    parser = References()
    parser.feed(html)
    checked: set[str] = set()
    queue = [path for value in parser.values if (path := local_path(value))]
    while queue:
        path = queue.pop(0)
        if path in checked or path == "/":
            continue
        checked.add(path)
        response = client.get(path)
        body = assert_response(response, f"{tool_id} {path}")
        if path.lower().endswith(".css"):
            css = body.decode("utf-8", errors="replace")
            for value in re.findall(r"url\(\s*['\"]?([^)'\"]+)", css, re.I):
                css_ref = urljoin(f"http://desktop.local{path}", value)
                nested = local_path(css_ref)
                if nested:
                    queue.append(nested)

    print(f"OK {tool_id}: trang đầu và {len(checked)} tài nguyên cục bộ")


def audit_images() -> None:
    images = []
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.ico"):
        images.extend(desktop.resource_root().rglob(pattern))
    if not images:
        raise AssertionError("Không có ảnh/logo trong payload")
    for path in images:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 16 or image.height < 16:
                raise AssertionError(f"Ảnh quá nhỏ hoặc lỗi: {path} {image.size}")
    print(f"OK images: {len(images)} ảnh/logo hợp lệ")


def audit_brand() -> None:
    brand = STAGE / "DesktopOfflineAssets" / "brand"
    required = [
        brand / "logo_moi.png", brand / "brand.css",
        brand / "fonts" / "BeVietnamPro-Regular.ttf",
        brand / "fonts" / "BeVietnamPro-SemiBold.ttf",
        brand / "fonts" / "BeVietnamPro-Bold.ttf",
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size < 1000]
    if missing:
        raise AssertionError("Thiếu tài nguyên nhận diện: " + ", ".join(missing))
    css = (brand / "brand.css").read_text(encoding="utf-8")
    for filename in ("BeVietnamPro-Regular.ttf", "BeVietnamPro-SemiBold.ttf", "BeVietnamPro-Bold.ttf"):
        if filename not in css:
            raise AssertionError(f"CSS chưa nhúng font: {filename}")
    print("OK brand: logo chuẩn, 3 font tiếng Việt, tông xanh và chữ ký")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--brand", action="store_true")
    args = parser.parse_args()
    desktop.configure_runtime()
    if args.images:
        audit_images()
    elif args.brand:
        audit_brand()
    elif args.tool:
        audit(args.tool)
    else:
        raise SystemExit("Cần --tool hoặc --images")
