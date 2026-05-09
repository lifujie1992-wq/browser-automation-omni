#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

_NUM = r'[-+]?\d+(?:,\d{3})*(?:\.\d+)?'
_MONEY = r'[¥￥]?\s*(' + _NUM + r')'


def _clean_num(s: str | None) -> float | int | None:
    if s is None:
        return None
    s = s.replace(',', '').replace('¥', '').replace('￥', '').strip()
    if not s or s == '-':
        return None
    try:
        v = float(s)
        return int(v) if v.is_integer() else v
    except ValueError:
        return None


def _first_card(cards: list[str], label: str) -> str | None:
    for c in cards:
        if label in c:
            return c
    return None


def _extract_metric_card(cards: list[str], label: str) -> dict[str, Any]:
    card = _first_card(cards, label)
    if not card:
        return {'label': label, 'raw': None, 'value': None}
    # label value 较昨日 trend ...
    after = card.split(label, 1)[1].strip()
    m = re.match(rf'({_NUM}|-)', after)
    value = _clean_num(m.group(1)) if m else None
    trend = None
    mt = re.search(r'较昨日\s*([^\s]+(?:\s*%)?|持平)', card)
    if mt:
        trend = mt.group(1).strip()
    benchmark = None
    mb = re.search(r'同行(?:基准值|中间值)\s*([¥￥]?[-\d,.]+\s*%?|[-])', card)
    if mb:
        benchmark = mb.group(1).strip()
    return {'label': label, 'value': value, 'trend_vs_yesterday': trend, 'benchmark': benchmark, 'raw': card}


def parse_doudian_home(snapshot: dict[str, Any]) -> dict[str, Any]:
    cards = snapshot.get('cards') or []
    all_text = '\n'.join(cards + (snapshot.get('relevantLines') or []))

    today_labels = [
        '用户支付金额', '成交订单数', '退款金额(支付时间)', '商品曝光人数', '商品点击人数',
        '成交人数', '客单价', '成交金额', '支出金额', '退款订单数(支付时间)',
        '退款金额(退款时间)', '退款订单数(退款时间)', '商品曝光-点击转化率(人数)',
        '商品点击-成交转化率(人数)', '结算金额', '投放消耗', '投放费比'
    ]
    today = {label: _extract_metric_card(cards, label) for label in today_labels}

    # Search overview
    search = {}
    search_card = _first_card(cards, '搜索数据概览')
    if search_card:
        patterns = {
            'search_pay_amount_7d': r'搜索用户支付金额\s*¥?(' + _NUM + r')',
            'search_pay_change': r'搜索用户支付金额\s*¥?' + _NUM + r'\s*较上周期\s*(' + _NUM + r'%)',
            'search_pay_share': r'占比本店\s*(' + _NUM + r'%)',
            'search_pay_peer_benchmark': r'同行标杆\s*¥?(' + _NUM + r')',
            'search_exposure_users': r'搜索曝光人数\s*([\d.]+万|[\d,.]+)',
            'search_exposure_change': r'搜索曝光人数\s*[\d.]+万?\s*较上周期\s*(' + _NUM + r'%)',
        }
        for k, p in patterns.items():
            m = re.search(p, search_card)
            search[k] = m.group(1) if m else None
        search['raw'] = search_card

    # Experience and funds
    exp = {}
    exp_card = _first_card(cards, '商家体验分')
    if exp_card:
        for k, p in {
            'score': r'商家体验分\s*(' + _NUM + r')\s*分',
            'product': r'商品\s*(' + _NUM + r')\s*分',
            'logistics': r'物流\s*(' + _NUM + r')\s*分',
            'service': r'服务\s*(' + _NUM + r')\s*分',
        }.items():
            m = re.search(p, exp_card)
            exp[k] = _clean_num(m.group(1)) if m else None
        exp['raw'] = exp_card

    funds = {}
    if exp_card:
        for k, p in {
            'basic_deposit': r'基础保证金\s*[¥￥]\s*(' + _NUM + r')',
            'experience_deposit_withdrawable': r'体验保证金\(可提现\)\s*[¥￥]\s*(' + _NUM + r')',
            'account_balance': r'账户资金\s*[¥￥]\s*(' + _NUM + r')',
        }.items():
            m = re.search(p, exp_card)
            funds[k] = _clean_num(m.group(1)) if m else None

    # Refund issues
    refund = {}
    refund_card = _first_card(cards, 'TOP退款原因')
    if refund_card:
        reasons = []
        for reason, amount, pct in re.findall(r'([^\s¥￥]+)\s*¥(' + _NUM + r')\((\d+)%\)', refund_card):
            if reason not in ['退款金额']:
                reasons.append({'reason': reason, 'amount': _clean_num(amount), 'percentage': int(pct)})
        refund['top_reasons'] = reasons
        refund['raw'] = refund_card
    m = re.search(r'近7天店铺退款率为(' + _NUM + r'%)', all_text)
    if m:
        refund['refund_rate_7d'] = m.group(1)
    m = re.search(r'7日退款金额：¥(' + _NUM + r')', all_text)
    if m:
        refund['refund_amount_7d'] = _clean_num(m.group(1))

    # Pending items labels (counts are often split in DOM; keep raw presence for now)
    pending_keywords = ['待支付', '待发货', '24h需发货', '异常包裹', '待处理售后', '临期待售后', '服务工单', '待整改风险点', '待处理违规']
    pending = {k: (k in all_text) for k in pending_keywords}

    result = {
        'source': {'title': snapshot.get('title'), 'url': snapshot.get('url')},
        'today': today,
        'search_7d': search,
        'experience': exp,
        'funds': funds,
        'refund': refund,
        'pending_presence': pending,
        'quality_hints': {
            'raw': _first_card(cards, '提升商品信息质量')
        }
    }
    return result
