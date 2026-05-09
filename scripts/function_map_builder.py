#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
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

from browser_omni_runtime.common.config import RUNTIME, load_platform_config
from browser_omni_runtime.common.io import atomic_write_json

REGISTRY = RUNTIME / 'contexts' / 'registry.json'
SCHEMA_DIR = RUNTIME / 'schemas'
LOG_DIR = RUNTIME / 'logs'
PY = Path(os.environ.get('CLOAKBROWSER_PY', str(Path.home() / 'github-tools' / 'CloakBrowser' / '.venv' / 'bin' / 'python')))
HARNESS = RUNTIME / 'scripts' / 'cdp_harness.py'

DOUDIAN_CONFIG = load_platform_config('doudian')
RISK_WORDS = DOUDIAN_CONFIG.get('risk_words', {})
HIGH_RISK_WORDS = RISK_WORDS.get('high', [
    '发布', '提交', '删除', '移除', '付款', '支付', '授权', '同意授权', '确认退款',
    '改价', '价格', '库存', '预算', '出价', '开启', '暂停', '批量', '结算', '提现'
])
QUERY_WORDS = RISK_WORDS.get('query', ['搜索', '查询', '筛选', '过滤', '日期', '时间', '关键词', '订单号', '手机号'])
DASHBOARD_WORDS = RISK_WORDS.get('dashboard', ['首页', '数据', '罗盘', '看板', '经营', '分析', '报表', '概览', '排行', '趋势'])
FORM_WORDS = RISK_WORDS.get('form', ['新建', '创建', '编辑', '填写', '上传', '发布商品', '商品发布', '素材'])
MONEY_WORDS = RISK_WORDS.get('money', ['千川', '推广', '投放', '预算', '出价', 'ROI', 'ROAS', '消耗', '账户资金', '保证金', '提现'])
LOGIN_WORDS = RISK_WORDS.get('login', ['登录', '扫码', '验证码', '密码', '短信', '手机验证', '设备验证'])


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def clean_text(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '').strip())[:100]


def classify_node(node: dict[str, Any]) -> tuple[str, str, list[str]]:
    text = clean_text(node.get('text') or node.get('id') or node.get('name') or node.get('href') or '')
    tag = node.get('tag', '')
    role = node.get('role', '')
    hay = text + ' ' + node.get('href', '') + ' ' + node.get('selector', '')
    risks: list[str] = []

    if any(w in hay for w in LOGIN_WORDS):
        return 'login_or_verification', 'human_required', ['login']
    if any(w in hay for w in HIGH_RISK_WORDS):
        risks.append('human_confirm_required')
    if any(w in hay for w in MONEY_WORDS):
        risks.append('money_related')
    if tag in ['input', 'textarea', 'select'] or any(w in hay for w in QUERY_WORDS):
        kind = 'query' if any(w in hay for w in QUERY_WORDS) else 'form_field'
    elif any(w in hay for w in DASHBOARD_WORDS):
        kind = 'dashboard'
    elif any(w in hay for w in FORM_WORDS):
        kind = 'form'
    elif tag == 'a' or role in ['menuitem', 'tab'] or node.get('href'):
        kind = 'navigation'
    elif tag == 'button' or role == 'button':
        kind = 'action'
    else:
        kind = 'unknown'

    risk = 'read_only'
    if 'human_confirm_required' in risks:
        risk = 'high'
    elif 'money_related' in risks:
        risk = 'medium'
    return kind, risk, risks


def stable_key(node: dict[str, Any]) -> str:
    text = clean_text(node.get('text', ''))
    selector = node.get('selector', '')
    href = node.get('href', '')
    return f"{text}|{selector}|{href}".lower()


def build_function_map(raw: dict[str, Any], profile: str) -> dict[str, Any]:
    seen = set()
    entrances = []
    for node in raw.get('nodes', []):
        text = clean_text(node.get('text', ''))
        if not text and not node.get('href') and not node.get('selector'):
            continue
        key = stable_key(node)
        if key in seen:
            continue
        seen.add(key)
        kind, risk, risk_flags = classify_node(node)
        entrances.append({
            'name': text or node.get('href') or node.get('selector'),
            'type': kind,
            'risk': risk,
            'risk_flags': risk_flags,
            'selector': node.get('selector', ''),
            'tag': node.get('tag', ''),
            'role': node.get('role', ''),
            'href': node.get('href', ''),
        })

    # group and rank: exact useful entrances first, noisy generic nodes later
    order = {'login_or_verification': 0, 'dashboard': 1, 'query': 2, 'navigation': 3, 'form': 4, 'action': 5, 'form_field': 6, 'unknown': 9}
    entrances.sort(key=lambda x: (order.get(x['type'], 9), x['risk'] == 'read_only', len(x['name'])))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for e in entrances:
        grouped.setdefault(e['type'], []).append(e)

    return {
        'profile': profile,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'page': {
            'title': raw.get('title'),
            'url': raw.get('url'),
            'login_hints': raw.get('loginHints', []),
        },
        'summary': {
            'total_entrances': len(entrances),
            'high_risk_count': sum(1 for e in entrances if e['risk'] == 'high'),
            'medium_risk_count': sum(1 for e in entrances if e['risk'] == 'medium'),
            'types': {k: len(v) for k, v in grouped.items()},
        },
        'entrances': entrances[:120],
        'grouped': {k: v[:40] for k, v in grouped.items()},
    }


def get_raw_map(profile: str, from_file: str | None) -> dict[str, Any]:
    if from_file:
        return json.loads(Path(from_file).read_text(encoding='utf-8'))
    cmd = [str(PY), str(HARNESS), 'map', '--profile', profile]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description='Build low-token function map / schema cache from CDP map output')
    parser.add_argument('--profile', default='doudian')
    parser.add_argument('--from-file')
    parser.add_argument('--out')
    args = parser.parse_args()

    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    raw = get_raw_map(args.profile, args.from_file)
    function_map = build_function_map(raw, args.profile)
    out = Path(args.out) if args.out else SCHEMA_DIR / f'{args.profile}-function-map.json'
    raw_out = LOG_DIR / f'{args.profile}-raw-map.json'
    atomic_write_json(out, function_map)
    atomic_write_json(raw_out, raw)
    print(json.dumps({'saved': str(out), 'raw_saved': str(raw_out), 'summary': function_map['summary']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
