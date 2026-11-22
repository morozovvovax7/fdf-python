"""Чтение и проверка файла карты высот формата .fdf.

Парсер не выводит сообщений и не завершает программу: при ошибке формата
он возбуждает MapFormatError, а отсутствие файла (OSError) пропускает
наружу — сообщение пользователю формирует main.py.
"""

import re
from collections.abc import Iterable
from pathlib import Path

from fdf.errors import FdfError, MapFormatError
from fdf.model import Map, Point

_INT_RE = re.compile(r"[+-]?\d+")
_COLOR_RE = re.compile(r"0[xX]([0-9a-fA-F]{1,6})")


def parse_color(text: str) -> str:
    """Преобразовать "0xRRGGBB" (ведущие нули можно опускать) в "#RRGGBB".

    >>> parse_color("0xff")
    '#0000FF'
    """
    match = _COLOR_RE.fullmatch(text)
    if match is None:
        raise ValueError(f"'{text}' — некорректный цвет (ожидается 0xRRGGBB)")
    return "#" + match.group(1).upper().rjust(6, "0")


def parse_value(token: str) -> tuple[int, str | None]:
    """Разобрать одно значение карты: "7", "-3", "2,0xFF8800", "1,0xff".

    Возвращает пару (высота, цвет или None). При ошибке — ValueError
    с описанием причины (без номера строки и колонки).
    """
    height_text, sep, color_text = token.partition(",")
    if _INT_RE.fullmatch(height_text) is None:
        raise ValueError(f"'{height_text}' — не целое число")
    height = int(height_text)
    if not sep:
        return height, None
    return height, parse_color(color_text)


def parse_lines(lines: Iterable[str]) -> Map:
    """Построить карту по строкам текста файла .fdf."""
    raw = [line.rstrip("\r\n") for line in lines]
    while raw and not raw[-1].strip():
        raw.pop()  # пустые строки в конце файла игнорируются
    if not raw:
        raise MapFormatError(1, 1, "файл карты пуст")

    rows: list[list[Point]] = []
    width: int | None = None
    for y, line in enumerate(raw):
        line_no = y + 1
        tokens = line.split()
        if not tokens:
            raise MapFormatError(line_no, 1, "пустая строка внутри карты")
        row: list[Point] = []
        for x, token in enumerate(tokens):
            try:
                z, color = parse_value(token)
            except ValueError as exc:
                raise MapFormatError(line_no, x + 1, str(exc)) from None
            row.append(Point(x, y, z, color))
        if width is None:
            width = len(row)
        elif len(row) != width:
            column = min(len(row), width) + 1
            raise MapFormatError(
                line_no,
                column,
                f"в строке {len(row)} знач., а в первой строке {width}",
            )
        rows.append(row)
    return Map(rows)


def load_map(path: str | Path) -> Map:
    """Прочитать карту из файла.

    OSError (файл не найден, нет прав и т. п.) не перехватывается.
    """
    try:
        with open(path, encoding="utf-8") as file:
            return parse_lines(file)
    except UnicodeDecodeError:
        raise FdfError("файл не является текстовым (ожидается UTF-8)") from None
