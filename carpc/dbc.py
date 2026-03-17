from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cantools


@lru_cache(maxsize=16)
def load_dbc(path: str) -> cantools.database.Database:
    p = Path(path)
    return cantools.database.load_file(str(p))

