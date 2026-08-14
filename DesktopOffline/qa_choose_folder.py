"""Kiểm tra cầu nối chọn thư mục native của bản desktop."""

import base64
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import main


api = main.ToolApi("http://127.0.0.1")
chosen = str(Path.home() / "Documents" / "Hồ sơ kiểm sát")
completed = SimpleNamespace(returncode=0, stdout=chosen, stderr="")
with patch.object(main.subprocess, "run", return_value=completed) as run_mock:
    result = api.choose_folder()
assert result == {"ok": True, "cancelled": False, "path": chosen}
command = run_mock.call_args.args[0]
assert command[0] == "powershell.exe"
assert "-STA" in command and "-EncodedCommand" in command
assert run_mock.call_args.kwargs["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Giải mã script để kiểm tra hộp thoại luôn hiện lên trước (owner form TopMost)
encoded = command[command.index("-EncodedCommand") + 1]
script = base64.b64decode(encoded).decode("utf-16le")
assert "$owner.TopMost = $true" in script, "Thiếu owner form TopMost"
assert "$owner.Activate()" in script, "Thiếu Activate() để đưa hộp thoại lên trước"
assert "$dialog.ShowDialog($owner)" in script, "Thiếu ShowDialog với owner"
assert "$owner.Dispose()" in script, "Thiếu Dispose() giải phóng form ẩn"

cancelled_process = SimpleNamespace(returncode=0, stdout="", stderr="")
with patch.object(main.subprocess, "run", return_value=cancelled_process):
    cancelled = api.choose_folder()
assert cancelled == {"ok": True, "cancelled": True, "path": ""}

print("OK chọn thư mục Windows STA: owner TopMost, giữ Unicode, ẩn console và xử lý hủy đúng")
