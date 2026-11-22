"""Модель данных: точка и карта высот.

Модуль не зависит ни от парсера, ни от графической библиотеки.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """Точка карты: x — позиция в строке, y — номер строки, z — высота.

    color — цвет из файла в виде строки "#RRGGBB" (верхний регистр) или None.
    """

    x: int
    y: int
    z: int
    color: str | None = None


class Map:
    """Прямоугольная сетка точек размером width × height."""

    def __init__(self, rows: Sequence[Sequence[Point]]) -> None:
        if not rows or not rows[0]:
            raise ValueError("карта должна содержать хотя бы одну точку")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("все строки карты должны быть одной длины")
        self._rows: tuple[tuple[Point, ...], ...] = tuple(tuple(row) for row in rows)
        self._width = width
        self._height = len(self._rows)
        heights = [p.z for p in self]
        self._z_min = min(heights)
        self._z_max = max(heights)

    @property
    def width(self) -> int:
        """Число точек в строке."""
        return self._width

    @property
    def height(self) -> int:
        """Число строк."""
        return self._height

    @property
    def z_min(self) -> int:
        """Минимальная высота на карте."""
        return self._z_min

    @property
    def z_max(self) -> int:
        """Максимальная высота на карте."""
        return self._z_max

    def __len__(self) -> int:
        return self._width * self._height

    def __iter__(self) -> Iterator[Point]:
        for row in self._rows:
            yield from row

    def __getitem__(self, key: tuple[int, int]) -> Point:
        x, y = key
        if not (0 <= x < self._width and 0 <= y < self._height):
            raise IndexError(f"точка ({x}, {y}) вне карты {self._width}×{self._height}")
        return self._rows[y][x]

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, Point):
            return False
        return (
            0 <= item.x < self._width
            and 0 <= item.y < self._height
            and self._rows[item.y][item.x] == item
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Map):
            return NotImplemented
        return self._rows == other._rows

    def __hash__(self) -> int:
        return hash(self._rows)

    def __repr__(self) -> str:
        return f"Map(width={self._width}, height={self._height})"

    def neighbors(self, point: Point) -> list[Point]:
        """Соседи точки по сетке: слева, справа, сверху, снизу (2–4 точки)."""
        result: list[Point] = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = point.x + dx, point.y + dy
            if 0 <= nx < self._width and 0 <= ny < self._height:
                result.append(self._rows[ny][nx])
        return result

    def edges(self) -> Iterator[tuple[Point, Point]]:
        """Рёбра каркаса: от каждой точки к соседу справа и к соседу снизу.

        Так каждое ребро встречается ровно один раз.
        """
        for y, row in enumerate(self._rows):
            for x, point in enumerate(row):
                if x + 1 < self._width:
                    yield point, row[x + 1]
                if y + 1 < self._height:
                    yield point, self._rows[y + 1][x]
