"""Исключения программы."""


class FdfError(Exception):
    """Базовое исключение программы FdF."""


class MapFormatError(FdfError):
    """Ошибка формата файла карты с указанием строки и колонки.

    Нумерация строк и колонок начинается с 1. Колонка — номер значения
    в строке (а не номер символа).
    """

    def __init__(self, line: int, column: int, message: str) -> None:
        self.line = line
        self.column = column
        self.message = message
        super().__init__(f"строка {line}, колонка {column}: {message}")
