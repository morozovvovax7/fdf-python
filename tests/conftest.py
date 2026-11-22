"""Общие фикстуры тестов."""

from pathlib import Path

import pytest

from fdf.model import Map
from fdf.parser import load_map

MAPS = Path(__file__).resolve().parent.parent / "maps"


@pytest.fixture
def maps_dir() -> Path:
    return MAPS


@pytest.fixture
def elem() -> Map:
    return load_map(MAPS / "elem.fdf")
