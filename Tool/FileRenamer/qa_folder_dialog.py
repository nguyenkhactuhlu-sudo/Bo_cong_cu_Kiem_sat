"""Kiểm tra cầu nối chọn thư mục Windows của FileRenamer portable."""

import sys
from types import SimpleNamespace
from unittest.mock import patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import file_renamer_gui as gui


selected = r"D:\Hồ sơ kiểm sát\Tài liệu"
completed = SimpleNamespace(returncode=0, stdout=selected, stderr="")
with patch.object(gui.subprocess, "run", return_value=completed) as run_mock:
    assert gui.browse_folder_windows() == selected
command = run_mock.call_args.args[0]
assert command[0] == "powershell.exe"
assert "-STA" in command and "-EncodedCommand" in command
assert run_mock.call_args.kwargs["creationflags"] == getattr(gui.subprocess, "CREATE_NO_WINDOW", 0)

# Giải mã script để kiểm tra hộp thoại luôn hiện lên trước (owner form TopMost)
import base64
encoded = command[command.index("-EncodedCommand") + 1]
script = base64.b64decode(encoded).decode("utf-16le")
assert "$owner.TopMost = $true" in script, "Thiếu owner form TopMost"
assert "$owner.Activate()" in script, "Thiếu Activate() để đưa hộp thoại lên trước"
assert "$dialog.ShowDialog($owner)" in script, "Thiếu ShowDialog với owner"
assert "$owner.Dispose()" in script, "Thiếu Dispose() giải phóng form ẩn"

# Kiểm tra cơ chế chống mở hộp thoại phía sau cửa sổ trình duyệt:
# form owner đặt giữa màn hình (không off-screen) để Windows cấp foreground hợp lệ.
assert '[System.Windows.Forms.FormStartPosition]::CenterScreen' in script, "Owner phải đặt giữa màn hình"
assert '$owner.Opacity = 0.01' in script, "Owner phải trong suốt để không hiện khung nhỏ"
assert 'SetForegroundWindow' in script, "Thiếu hàm SetForegroundWindow chiếm foreground"
assert '$dialog.UseDescriptionForTitle = $true' in script, "Thiếu dùng title mô tả cho hộp thoại"
assert '$owner.Left = -32000' not in script, "Không còn đặt owner off-screen"

with patch.object(gui, "browse_folder_windows", return_value=selected):
    response = gui.app.test_client().get("/api/browse-folder")
assert response.status_code == 200
assert response.get_json() == {"path": selected}

print("OK chọn thư mục: STA, console ẩn, owner TopMost, endpoint giữ Unicode")