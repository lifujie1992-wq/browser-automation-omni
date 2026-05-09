from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Cross-platform file locking
if sys.platform == "win32":
    import msvcrt

    def _lock_file(fd: int, exclusive: bool = True) -> None:
        msvcrt.locking(fd, msvcrt.LK_LOCK if exclusive else msvcrt.LK_NBLCK, 1)

    def _unlock_file(fd: int) -> None:
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock_file(fd: int, exclusive: bool = True) -> None:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_NB)

    def _unlock_file(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def atomic_write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=indent))


def locked_append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + '.lock')
    with lock_path.open('w', encoding='utf-8') as lock:
        _lock_file(lock.fileno())
        try:
            with path.open('a', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
        finally:
            _unlock_file(lock.fileno())


def locked_append_jsonl(path: Path, data: dict[str, Any]) -> None:
    locked_append_text(path, json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
