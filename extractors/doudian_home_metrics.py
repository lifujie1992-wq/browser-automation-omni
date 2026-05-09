#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
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

SNAPSHOT = RUNTIME / 'logs' / 'doudian-dashboard-snapshot.json'
OUT = RUNTIME / 'logs' / 'doudian-home-metrics.json'
DOUDIAN_CONFIG = load_platform_config('doudian')
METRIC_LABELS: dict[str, str] = DOUDIAN_CONFIG.get('metric_labels', {})


def parse_money(s: str) -> float | None:
    m = re.search(r'[¥￥]\s*([0-9,.]+)', s)
    if not m:
        return None
    return float(m.group(1).replace(',', ''))


def parse_number_after(label: str, s: str) -> str | None:
    m = re.search(re.escape(label) + r'\s*([\-0-9.]+\s*%?|[¥￥]\s*[0-9,.]+|[0-9.]+万)', s)
    return m.group(1).strip() if m else None


def as_num(v: str | None) -> float | int | str | None:
    if v is None:
        return None
    raw = v.strip().replace(',', '')
    if raw in ['-', '—', '']:
        return raw
    if raw.endswith('%'):
        return raw
    if raw.startswith(('¥', '￥')):
        try:
            return float(raw[1:].strip())
        except ValueError:
            return v
    if raw.endswith('万'):
        try:
            return float(raw[:-1]) * 10000
        except ValueError:
            return v
    try:
        f = float(raw)
        return int(f) if f.is_integer() else f
    except ValueError:
        return v


def find_card(cards: list[str], prefix: str) -> str | None:
    for c in cards:
        if c.startswith(prefix):
            return c
    return None


def parse_cards(cards: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {
        'today': {},
        'search_7d': {},
        'experience': {},
        'funds': {},
        'refund': {},
        'quality': {},
        'raw_cards_used': []
    }
    mapping = METRIC_LABELS or {
        '用户支付金额': 'user_pay_amount',
        '成交订单数': 'order_count',
        '退款金额(支付时间)': 'refund_amount_by_pay_time',
        '商品曝光人数': 'product_exposure_users',
        '商品点击人数': 'product_click_users',
        '成交人数': 'buyer_count',
        '客单价': 'avg_order_value',
        '成交金额': 'transaction_amount',
        '支出金额': 'expense_amount',
        '退款订单数(支付时间)': 'refund_orders_by_pay_time',
        '退款金额(退款时间)': 'refund_amount_by_refund_time',
        '退款订单数(退款时间)': 'refund_orders_by_refund_time',
        '商品曝光-点击转化率(人数)': 'exposure_to_click_rate',
        '商品点击-成交转化率(人数)': 'click_to_order_rate',
        '结算金额': 'settlement_amount',
        '投放消耗': 'ad_spend',
        '投放费比': 'ad_cost_ratio',
    }
    for label, key in mapping.items():
        c = find_card(cards, label)
        if c:
            val = parse_number_after(label, c)
            out['today'][key] = as_num(val)
            out['raw_cards_used'].append(c)
            # extract yesterday trend if present
            mt = re.search(r'较昨日\s*([^\s]+)', c)
            if mt:
                out['today'][key + '_vs_yesterday'] = mt.group(1)
            mb = re.search(r'同行(?:基准值|中间值)\s*([^\s]+)', c)
            if mb:
                out['today'][key + '_peer_benchmark'] = as_num(mb.group(1))

    search = next((c for c in cards if c.startswith('搜索数据概览 近7天 搜索用户支付金额')), None)
    if search:
        out['raw_cards_used'].append(search)
        patterns = {
            'search_pay_amount': r'搜索用户支付金额\s*([¥￥]\s*[0-9,.]+)',
            'search_pay_vs_prev_period': r'较上周期\s*([0-9.]+%)',
            'search_pay_ratio_of_shop': r'占比本店\s*([0-9.]+%)',
            'search_pay_peer_benchmark': r'同行标杆\s*([¥￥]\s*[0-9,.]+)',
            'search_exposure_users': r'搜索曝光人数\s*([0-9.]+万|[0-9,.]+)',
            'search_exposure_vs_prev_period': r'搜索曝光人数.*?较上周期\s*([0-9.]+%)',
            'search_exposure_peer_benchmark': r'搜索曝光人数.*?同行标杆\s*([0-9.]+万|[0-9,.]+)',
        }
        for k, pat in patterns.items():
            m = re.search(pat, search)
            out['search_7d'][k] = as_num(m.group(1)) if m else None

    exp = next((c for c in cards if c.startswith('商家体验分') or '商家体验分 69' in c), None)
    if exp:
        out['raw_cards_used'].append(exp)
        for k, pat in {
            'merchant_experience_score': r'商家体验分\s*([0-9]+)\s*分',
            'product_score': r'商品\s*([0-9]+)\s*分',
            'logistics_score': r'物流\s*([0-9]+)\s*分',
            'service_score': r'服务\s*([0-9]+)\s*分',
            'basic_deposit': r'基础保证金\s*[¥￥]\s*([0-9,.]+)',
            'experience_deposit_withdrawable': r'体验保证金\(可提现\)\s*[¥￥]\s*([0-9,.]+)',
            'account_balance': r'账户资金\s*[¥￥]\s*([0-9,.]+)',
        }.items():
            m = re.search(pat, exp)
            if m:
                val = m.group(1)
                out['experience' if 'score' in k else 'funds'][k] = as_num(val)

    refund = next((c for c in cards if c.startswith('TOP退款原因')), None)
    if refund:
        out['raw_cards_used'].append(refund)
        reasons = re.findall(r'([^\s]+(?:信息不符|缺货|用户权益))\s*[¥￥]\s*([0-9,.]+)\(([0-9]+%)\)', refund)
        out['refund']['top_reasons'] = [{'reason': r, 'amount': float(a.replace(',', '')), 'ratio': pct} for r, a, pct in reasons]

    quality = next((c for c in cards if c.startswith('提升商品信息质量')), None)
    if quality:
        out['raw_cards_used'].append(quality)
        for k, pat in {
            'failed_product_count': r'不及格商品数\s*([0-9]+)',
            'passed_product_count': r'及格商品数\s*([0-9]+)',
            'excellent_product_count': r'优秀商品数\s*([0-9]+)',
        }.items():
            m = re.search(pat, quality)
            if m:
                out['quality'][k] = int(m.group(1))

    return out


def build_summary(metrics: dict[str, Any]) -> list[str]:
    t = metrics.get('today', {})
    e = metrics.get('experience', {})
    s = metrics.get('search_7d', {})
    lines = []
    if t.get('user_pay_amount') == 0 and t.get('order_count') == 0:
        lines.append('今日目前无成交：支付金额 0，成交订单数 0。')
    if t.get('product_exposure_users') is not None:
        lines.append(f"今日商品曝光人数 {t.get('product_exposure_users')}，较昨日 {t.get('product_exposure_users_vs_yesterday')}。")
    if t.get('product_click_users') is not None:
        lines.append(f"今日商品点击人数 {t.get('product_click_users')}，较昨日 {t.get('product_click_users_vs_yesterday')}。")
    if t.get('ad_spend') is not None:
        lines.append(f"今日投放消耗 {t.get('ad_spend')}，较昨日 {t.get('ad_spend_vs_yesterday')}。")
    if e.get('merchant_experience_score') is not None:
        lines.append(f"商家体验分 {e.get('merchant_experience_score')}，商品 {e.get('product_score')}，物流 {e.get('logistics_score')}，服务 {e.get('service_score')}。")
    if s.get('search_pay_amount') is not None:
        lines.append(f"近7天搜索支付金额 {s.get('search_pay_amount')}，较上周期 {s.get('search_pay_vs_prev_period')}，同行标杆 {s.get('search_pay_peer_benchmark')}。")
    return lines


def main() -> None:
    snap = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    snapshot = snap.get('snapshot', snap)
    cards = snapshot.get('cards', [])
    metrics = parse_cards(cards)
    metrics['meta'] = {
        'source_snapshot': str(SNAPSHOT),
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'title': snapshot.get('title'),
        'url': snapshot.get('url'),
        'extractor': str(Path(__file__).resolve())
    }
    metrics['summary'] = build_summary(metrics)
    atomic_write_json(OUT, metrics)
    print(json.dumps({'saved': str(OUT), 'metrics': metrics}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
