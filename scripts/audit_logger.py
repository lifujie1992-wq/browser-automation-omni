#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from browser_omni_runtime.common.config import RUNTIME
from browser_omni_runtime.common.io import locked_append_jsonl

AUDIT_DIR = RUNTIME / 'logs' / 'audit'


def log_event(event: dict[str, Any]) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    payload = {
        'time': now.isoformat(timespec='seconds'),
        **event,
    }
    path = AUDIT_DIR / f'{now.date().isoformat()}.jsonl'
    locked_append_jsonl(path, payload)
    return path
