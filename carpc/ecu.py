from __future__ import annotations

import cantools


def build_message_data(
    *,
    dbc: cantools.database.Database,
    message_name: str,
    signals: dict[str, float | int],
) -> tuple[int, bytes]:
    msg = dbc.get_message_by_name(message_name)
    payload = msg.encode(signals)
    return msg.frame_id, payload

