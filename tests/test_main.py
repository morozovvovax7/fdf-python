"""Тесты точки входа: справка, диагностика и коды возврата (без открытия окна)."""

from pathlib import Path

import pytest

from main import EXIT_ERROR, EXIT_USAGE, main


@pytest.mark.parametrize("argv", [["main.py"], ["main.py", "a.fdf", "b.fdf"]])
def test_usage(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(argv) == EXIT_USAGE
    assert "Использование" in capsys.readouterr().err


def test_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["main.py", str(tmp_path / "nope.fdf")]) == EXIT_ERROR
    assert "не удалось открыть файл" in capsys.readouterr().err


def test_bad_format(maps_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["main.py", str(maps_dir / "bad" / "not_int.fdf")]) == EXIT_ERROR
    assert "строка 2, колонка 3" in capsys.readouterr().err
