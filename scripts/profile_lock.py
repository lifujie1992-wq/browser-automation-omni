#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from browser_omni_runtime.common.config import RUNTIME
from browser_omni_runtime.common.io import atomic_write_json

LOCK_DIR = RUNTIME / 'state' / 'locks'
REGISTRY = RUNTIME / 'contexts' / 'registry.json'


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def lock_path(profile: str) -> Path:
    return LOCK_DIR / f'{profile}.lock.json'


def load_lock(profile: str) -> dict[str, Any] | None:
    p = lock_path(profile)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {'corrupt': True, 'path': str(p)}
    pid = int(data.get('pid') or 0)
    data['alive'] = bool(pid and pid_alive(pid))
    return data


def acquire(profile: str, owner: str, force: bool = False) -> dict[str, Any]:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_lock(profile)
    if existing and existing.get('alive') and not force:
        raise SystemExit(json.dumps({'ok': False, 'error': 'profile_locked', 'lock': existing}, ensure_ascii=False, indent=2))
    data = {
        'profile': profile,
        'owner': owner,
        'pid': os.getpid(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
    }
    atomic_write_json(lock_path(profile), data)
    return data


def release(profile: str, owner: str | None = None, force: bool = False) -> dict[str, Any]:
    p = lock_path(profile)
    if not p.exists():
        return {'ok': True, 'released': False, 'reason': 'no_lock'}
    data = load_lock(profile) or {}
    if owner and data.get('owner') != owner and not force:
        raise SystemExit(json.dumps({'ok': False, 'error': 'owner_mismatch', 'lock': data}, ensure_ascii=False, indent=2))
    p.unlink()
    return {'ok': True, 'released': True, 'lock': data}


def main() -> None:
    parser = argparse.ArgumentParser(description='Profile lock helper to avoid concurrent profile operations')
    parser.add_argument('action', choices=['status', 'acquire', 'release'])
    parser.add_argument('--profile', default='doudian')
    parser.add_argument('--owner', default='manual')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.action == 'status':
        print(json.dumps({'lock': load_lock(args.profile), 'path': str(lock_path(args.profile))}, ensure_ascii=False, indent=2))
    elif args.action == 'acquire':
        print(json.dumps({'ok': True, 'lock': acquire(args.profile, args.owner, args.force)}, ensure_ascii=False, indent=2))
    elif args.action == 'release':
        print(json.dumps(release(args.profile, args.owner, args.force), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
