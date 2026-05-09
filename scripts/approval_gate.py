#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from browser_omni_runtime.common.config import RUNTIME, load_profile
from browser_omni_runtime.common.io import locked_append_jsonl

LOG_DIR = RUNTIME / 'logs' / 'audit'

DEFAULT_RISK_WORDS = {
    'login': ['登录', '扫码', '验证码', '密码', '短信', '2FA'],
    'submit': ['提交', '确认', '保存并提交'],
    'publish': ['发布', '上架', '立即发布'],
    'delete': ['删除', '移除', '清空'],
    'price_change': ['改价', '价格', '售价'],
    'inventory_change': ['库存', '现货'],
    'budget_change': ['预算', '日限额', '计划预算'],
    'bid_change': ['出价', '竞价'],
    'authorization': ['授权', 'OAuth', '同意授权'],
    'payment': ['付款', '支付', '提现', '结算'],
}


def detect_risk(action: str, text: str, profile: dict[str, Any]) -> list[str]:
    hay = f'{action} {text}'.lower()
    policy = profile.get('risk_policy', {})
    required = set(policy.get('human_confirm_required', []))
    hits: list[str] = []
    for risk, words in DEFAULT_RISK_WORDS.items():
        if risk in required and any(w.lower() in hay for w in words):
            hits.append(risk)
    # also honor explicit action names
    for risk in required:
        if risk.lower() in hay and risk not in hits:
            hits.append(risk)
    return hits


def append_audit(event: dict[str, Any]) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    locked_append_jsonl(path, event)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description='Human approval gate and audit event writer')
    parser.add_argument('--profile', default='doudian')
    parser.add_argument('--action', required=True, help='Action name, e.g. click_publish/read_dashboard')
    parser.add_argument('--target', default='', help='Selector, URL, button text, or logical target')
    parser.add_argument('--mode', choices=['read', 'write'], default='read')
    parser.add_argument('--before', default='', help='Before-state summary or JSON string')
    parser.add_argument('--after', default='', help='After-state summary or JSON string')
    parser.add_argument('--result', default='planned')
    parser.add_argument('--confirmed-by-human', action='store_true')
    parser.add_argument('--reason', default='')
    args = parser.parse_args()

    profile = load_profile(args.profile)
    risk_hits = detect_risk(args.action, args.target + ' ' + args.before + ' ' + args.after, profile)
    blocked = bool(risk_hits) and not args.confirmed_by_human
    event = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'profile': args.profile,
        'platform': profile.get('platform'),
        'url': profile.get('target_url'),
        'action': args.action,
        'target': args.target,
        'mode': args.mode,
        'risk_hits': risk_hits,
        'requires_human_approval': bool(risk_hits),
        'confirmed_by_human': args.confirmed_by_human,
        'blocked': blocked,
        'before': args.before,
        'after': args.after,
        'result': 'blocked_need_human_confirmation' if blocked else args.result,
        'reason': args.reason,
    }
    audit_path = append_audit(event)
    print(json.dumps({'audit_log': str(audit_path), 'event': event}, ensure_ascii=False, indent=2))
    if blocked:
        sys.exit(2)


if __name__ == '__main__':
    main()
