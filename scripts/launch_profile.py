#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
from datetime import datetime
from pathlib import Path
import sys

from cloakbrowser import launch_persistent_context

from browser_omni_runtime.common.config import RUNTIME, load_profile, resolve_profile
from browser_omni_runtime.common.io import atomic_write_json, locked_append_text

STATE_DIR = RUNTIME / 'state'
LOG_DIR = RUNTIME / 'logs'


def write_state(name: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state['updated_at'] = datetime.now().isoformat(timespec='seconds')
    atomic_write_json(STATE_DIR / f'{name}.json', state)


def main() -> int:
    parser = argparse.ArgumentParser(description='Launch CloakBrowser persistent profile with fixed CDP port')
    parser.add_argument('--profile', default='doudian')
    parser.add_argument('--url', default=None)
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()

    profile = resolve_profile(load_profile(args.profile))
    profile_dir = Path(profile['profile_dir'])
    profile_dir.mkdir(parents=True, exist_ok=True)
    cdp_port = int(profile['cdp_port'])
    url = args.url or profile['target_url']

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f'{args.profile}-launcher.log'

    ctx = None
    closed = False

    def log(msg: str) -> None:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
        print(line, flush=True)
        locked_append_text(log_path, line + '\n')

    def shutdown(signum=None, frame=None):
        nonlocal closed
        if closed:
            return
        closed = True
        log(f'Shutting down profile={args.profile}')
        try:
            if ctx:
                ctx.close()
        finally:
            write_state(args.profile, {'status': 'stopped', 'profile': args.profile, 'pid': None, 'cdp_port': cdp_port})
            sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    extra_args = [
        f'--remote-debugging-port={cdp_port}',
        '--remote-allow-origins=*',
        '--window-size=1440,900',
    ]

    log(f'Launching CloakBrowser profile={args.profile} profile_dir={profile_dir} cdp_port={cdp_port}')
    ctx = launch_persistent_context(
        str(profile_dir),
        headless=bool(args.headless),
        humanize=True,
        viewport={'width': 1440, 'height': 900},
        locale=profile.get('locale', 'zh-CN'),
        timezone=profile.get('timezone', 'Asia/Shanghai'),
        args=extra_args,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    state = {
        'status': 'running',
        'profile': args.profile,
        'platform': profile['platform'],
        'pid': None,
        'cdp_port': cdp_port,
        'profile_dir': str(profile_dir),
        'url': page.url,
        'title': page.title(),
        'launcher': str(Path(__file__).resolve()),
        'log': str(log_path),
    }
    write_state(args.profile, state)
    log(f'CloakBrowser ready profile={args.profile} title={page.title()} url={page.url} cdp=http://127.0.0.1:{cdp_port}')
    log('Keep this process running. Send Enter or SIGTERM to close context.')

    try:
        while True:
            time.sleep(2)
    finally:
        shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
