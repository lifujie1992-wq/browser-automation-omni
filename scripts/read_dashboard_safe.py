#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from browser_omni_runtime.common.config import RUNTIME
from browser_omni_runtime.common.io import atomic_write_json

LOG_DIR = RUNTIME / 'logs'
PY = Path(os.environ.get('CLOAKBROWSER_PY', str(Path.home() / 'github-tools' / 'CloakBrowser' / '.venv' / 'bin' / 'python')))
HARNESS = RUNTIME / 'scripts' / 'cdp_harness.py'
METRICS = RUNTIME / 'extractors' / 'doudian_home_metrics.py'
FALLBACK_OUT = LOG_DIR / 'vision-fallback-note.json'


def run(cmd: list[str], timeout: int = 90) -> tuple[int, str, str]:
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def main() -> None:
    parser = argparse.ArgumentParser(description='Read dashboard with CDP first; record CuaDriver/vision fallback policy if CDP fails')
    parser.add_argument('--profile', default='doudian')
    args = parser.parse_args()

    status_code, status_out, status_err = run([str(PY), str(HARNESS), 'status', '--profile', args.profile], 45)
    if status_code == 0:
        dash_code, dash_out, dash_err = run([str(PY), str(HARNESS), 'dashboard', '--profile', args.profile], 90)
        if dash_code == 0:
            metric_code, metric_out, metric_err = run([str(PY), str(METRICS)], 30)
            if metric_code == 0:
                print(metric_out)
                return
            raise SystemExit(metric_err or metric_out)

    # Do not automate CuaDriver from inside this script because MCP tools are outside Python subprocess.
    # Instead emit an explicit fallback instruction for the agent/operator.
    note = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'profile': args.profile,
        'primary': 'CDP dashboard extraction failed',
        'status_stdout': status_out[-1000:],
        'status_stderr': status_err[-1000:],
        'fallback_policy': {
            'allowed': True,
            'tool': 'CuaDriver + screenshot/vision',
            'when': [
                'CDP port unreachable',
                'DOM does not expose canvas/chart/native dialog data',
                'selector drift or unknown visual modal',
                'need visual verification after a risky UI state change'
            ],
            'rules': [
                'vision is a兜底, not forbidden',
                'prefer CDP/DOM for structured text when available',
                'save screenshot path and mark extracted fields as visual_source',
                'do not execute high-risk actions from vision guess without approval_gate'
            ]
        }
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(FALLBACK_OUT, note)
    print(json.dumps({'needs_visual_fallback': True, 'saved': str(FALLBACK_OUT), 'note': note}, ensure_ascii=False, indent=2))
    raise SystemExit(3)


if __name__ == '__main__':
    main()
