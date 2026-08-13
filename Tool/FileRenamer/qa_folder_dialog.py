"""Kiểm tra cầu nối chọn thư mục Windows của FileRenamer portable."""

from types import SimpleNamespace
from unittest.mock import patch

import file_renamer_gui as gui


selected = r"D:\Hồ sơ kiểm sát\Tài liệu"
completed = SimpleNamespace(returncode=0, stdout=selected, stderr="")
with patch.object(gui.subprocess, "run", return_value=completed) as run_mock:
    assert gui.browse_folder_windows() == selected
command = run_mock.call_args.args[0]
assert command[0] == "powershell.exe"
assert "-STA" in command and "-EncodedCommand" in command
assert run_mock.call_args.kwargs["creationflags"] == getattr(gui.subprocess, "CREATE_NO_WINDOW", 0)

with patch.object(gui, "browse_folder_windows", return_value=selected):
    response = gui.app.test_client().get("/api/browse-folder")
assert response.status_code == 200
assert response.get_json() == {"path": selected}

print("OK chọn thư mục: STA, console ẩn, endpoint giữ Unicode")
