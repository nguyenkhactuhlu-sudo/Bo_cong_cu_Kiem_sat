"""Kiểm tra cầu nối chọn thư mục native của bản desktop."""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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

cancelled_process = SimpleNamespace(returncode=0, stdout="", stderr="")
with patch.object(main.subprocess, "run", return_value=cancelled_process):
    cancelled = api.choose_folder()
assert cancelled == {"ok": True, "cancelled": True, "path": ""}

print("OK chọn thư mục Windows STA: giữ Unicode, ẩn console và xử lý hủy đúng")
