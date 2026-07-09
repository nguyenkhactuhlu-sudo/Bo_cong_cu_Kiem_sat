# -*- coding: utf-8 -*-
"""
auto_install.py - Module dùng chung để kiểm tra và tự động cài thư viện Python thiếu
====================================================================================
Dùng cho tất cả các tool GUI trong bộ công cụ (PdfToMd, DocxToMd, FileRenamer).

Cách dùng:
    from auto_install import check_and_install

    # Khai báo dict {module_name: pip_package_name}
    check_and_install({
        "flask": "flask",
        "docx": "python-docx",
    })

Lưu ý:
- Khi chạy file .py: tự động pip install thư viện thiếu rồi restart script
- Khi chạy file .exe (đã build sẵn): code này không chạy vì mọi thứ đã có trong .exe
"""

import sys
import subprocess
import importlib


def check_and_install(required: dict):
    """
    Kiểm tra và tự động cài thư viện Python còn thiếu.

    Args:
        required: dict dạng {module_name: pip_package_name}
                  VD: {"flask": "flask", "pypdf": "pypdf"}

    Nếu thiếu thư viện:
        - Tự động chạy pip install
        - Thoát script để người dùng chạy lại (lần sau import sẽ OK)
    Nếu đủ: trả về không làm gì.
    """
    missing = []
    for mod, pip_name in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return  # Đã đủ hết

    print(f"[SETUP] Thiếu thư viện: {', '.join(missing)}")
    print("[SETUP] Đang tự động cài đặt, vui lòng đợi...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"] + missing,
            stdout=sys.stdout, stderr=sys.stderr
        )
        print("[SETUP] Cài đặt thành công! Vui lòng chạy lại lệnh.")
        # Thoát để user chạy lại script, lần sau sẽ import thành công
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Không thể tự động cài thư viện: {e}")
        print("[INFO] Vui lòng chạy lệnh sau trong Terminal/CMD rồi thử lại:")
        print(f"    pip install {' '.join(missing)}")
        input("Nhấn Enter để thoát...")
        sys.exit(1)