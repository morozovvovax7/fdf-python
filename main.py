"""Точка входа: python main.py <файл.fdf>."""

import sys
from pathlib import Path

from fdf.errors import FdfError
from fdf.parser import load_map

USAGE = "Использование: python main.py <файл.fdf>"
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def main(argv: list[str]) -> int:
    """Разобрать аргументы, загрузить карту и открыть окно. Возвращает код выхода."""
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE

    path = Path(argv[1])
    try:
        map_ = load_map(path)
    except FdfError as exc:
        print(f"fdf: {path}: ошибка формата карты: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        reason = exc.strerror or str(exc)
        print(f"fdf: {path}: не удалось открыть файл: {reason}", file=sys.stderr)
        return EXIT_ERROR

    try:
        from fdf.app import App  # графика нужна только после загрузки карты
    except ImportError as exc:
        print(f"fdf: графическая библиотека недоступна: {exc}", file=sys.stderr)
        return EXIT_ERROR

    try:
        app = App(map_, title=f"FdF — {path.name}")
        app.run()
    except KeyboardInterrupt:
        return EXIT_OK
    except Exception as exc:  # например, tk.TclError: нет дисплея
        print(f"fdf: не удалось открыть окно: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
