from __future__ import annotations

import logging
import os
from typing import Literal


LogFormat = Literal["plain", "json"]


def setup_logging(level: str = "INFO", fmt: LogFormat | None = None) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    chosen = (fmt or os.getenv("CARPC_LOG_FORMAT", "plain")).lower()

    if chosen == "json":
        logging.basicConfig(
            level=lvl,
            format='{"ts":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}',
        )
    else:
        logging.basicConfig(
            level=lvl,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )

