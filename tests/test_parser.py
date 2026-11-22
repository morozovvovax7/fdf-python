"""Тесты парсера карты."""

from pathlib import Path

import pytest

from fdf.errors import FdfError, MapFormatError
from fdf.model import Map
from fdf.parser import load_map, parse_color, parse_lines, parse_value


def test_elem_size_and_center(elem: Map) -> None:
    assert (elem.width, elem.height) == (5, 5)
    assert elem[2, 2].z == 5


def test_elem_coordinates_match_file_positions(elem: Map) -> None:
    for y in range(elem.height):
        for x in range(elem.width):
            point = elem[x, y]
            assert (point.x, point.y) == (x, y)
    assert elem[1, 2].z == 2
    assert elem[0, 4].z == 0


def test_42_map(maps_dir: Path) -> None:
    m = load_map(maps_dir / "42.fdf")
    assert (m.width, m.height) == (19, 11)
    assert (m.z_min, m.z_max) == (0, 10)


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("7", (7, None)),
        ("-3", (-3, None)),
        ("2,0xFF8800", (2, "#FF8800")),
        ("1,0xff", (1, "#0000FF")),
        ("0,0xFF00", (0, "#00FF00")),
        ("4,0XaBcDeF", (4, "#ABCDEF")),
    ],
)
def test_parse_value(token: str, expected: tuple[int, str | None]) -> None:
    assert parse_value(token) == expected


@pytest.mark.parametrize("token", ["x", "1.5", "", "1,", "1,ff", "1,0x", "1,0x1234567"])
def test_parse_value_rejects(token: str) -> None:
    with pytest.raises(ValueError):
        parse_value(token)


def test_parse_color_short_form() -> None:
    assert parse_color("0xff") == "#0000FF"
    assert parse_color("0x802020") == "#802020"


def test_trailing_blank_lines_ignored() -> None:
    m = parse_lines(["1 2\n", "3 4\n", "\n", "   \n"])
    assert (m.width, m.height) == (2, 2)


def test_multiple_spaces_and_tabs() -> None:
    m = parse_lines(["  1    2\t3  \n"])
    assert [p.z for p in m] == [1, 2, 3]


def test_partial_colors() -> None:
    m = parse_lines(["0 10,0xff0000 0"])
    assert [p.color for p in m] == [None, "#FF0000", None]


@pytest.mark.parametrize("name", ["empty.fdf", "only_blank.fdf"])
def test_empty_file(maps_dir: Path, name: str) -> None:
    with pytest.raises(MapFormatError, match="пуст"):
        load_map(maps_dir / "bad" / name)


def test_not_int(maps_dir: Path) -> None:
    with pytest.raises(MapFormatError) as info:
        load_map(maps_dir / "bad" / "not_int.fdf")
    assert (info.value.line, info.value.column) == (2, 3)
    assert str(info.value) == "строка 2, колонка 3: 'x' — не целое число"


def test_ragged_rows(maps_dir: Path) -> None:
    with pytest.raises(MapFormatError) as info:
        load_map(maps_dir / "bad" / "ragged.fdf")
    assert info.value.line == 2


@pytest.mark.parametrize("name", ["bad_color.fdf", "long_color.fdf"])
def test_bad_color(maps_dir: Path, name: str) -> None:
    with pytest.raises(MapFormatError) as info:
        load_map(maps_dir / "bad" / name)
    assert (info.value.line, info.value.column) == (2, 2)
    assert "цвет" in str(info.value)


def test_blank_line_inside(maps_dir: Path) -> None:
    with pytest.raises(MapFormatError) as info:
        load_map(maps_dir / "bad" / "blank_line.fdf")
    assert info.value.line == 2


def test_map_format_error_is_fdf_error() -> None:
    assert issubclass(MapFormatError, FdfError)


def test_missing_file_raises_oserror(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        load_map(tmp_path / "nope.fdf")


def test_binary_file(tmp_path: Path) -> None:
    path = tmp_path / "bin.fdf"
    path.write_bytes(b"\xff\xfe\x00\x81")
    with pytest.raises(FdfError):
        load_map(path)
