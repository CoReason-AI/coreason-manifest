with open("tests/scripts/test_watchdog.py", "r") as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "def test_main_file_error(mock_open: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:" in lines[i]:
        lines[i] = lines[i].replace("mock_open: MagicMock, ", "")

with open("tests/scripts/test_watchdog.py", "w") as f:
    f.writelines(lines)
