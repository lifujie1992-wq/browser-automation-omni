#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Any

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.async_api import async_playwright

from browser_omni_runtime.common.config import RUNTIME, load_platform_config, load_profile
from browser_omni_runtime.common.io import atomic_write_json
from browser_omni_runtime.common.retry import async_retry

OUT_DIR = RUNTIME / 'logs'


def compact_print(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


PAGE_MAP_JS = r"""
(() => {
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const clean = s => (s || '').trim().replace(/\s+/g, ' ').slice(0, 100);
  const selectorFor = el => {
    if (el.id) return '#' + CSS.escape(el.id);
    const dataKeys = ['data-e2e','data-testid','data-test','data-role','data-menu-id'];
    for (const k of dataKeys) {
      const v = el.getAttribute(k);
      if (v) return `${el.tagName.toLowerCase()}[${k}="${CSS.escape(v)}"]`;
    }
    const txt = clean(el.innerText || el.getAttribute('aria-label') || el.title || el.placeholder || el.value);
    return `${el.tagName.toLowerCase()}${txt ? ':text(' + JSON.stringify(txt.slice(0, 30)) + ')' : ''}`;
  };
  const nodes = [...document.querySelectorAll('a,button,input,textarea,select,[role=button],[role=tab],[role=menuitem],[class*=menu],[class*=nav]')]
    .filter(visible)
    .slice(0, 180)
    .map(el => ({
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      text: clean(el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || el.title),
      id: el.id || '',
      name: el.getAttribute('name') || '',
      type: el.getAttribute('type') || '',
      href: el.getAttribute('href') || '',
      selector: selectorFor(el)
    }))
    .filter(x => x.text || x.id || x.name || x.href);
  const bodyText = clean(document.body?.innerText || '').slice(0, 500);
  const loginHints = ['登录','扫码','验证码','密码','手机','短信'].filter(t => (document.body?.innerText || '').includes(t));
  return {title: document.title, url: location.href, loginHints, nodes, bodyText};
})()
"""

DASHBOARD_JS = r"""
(() => {
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const clean = s => (s || '').trim().replace(/\s+/g, ' ').slice(0, 160);
  const text = document.body?.innerText || '';
  const lines = text.split('\n').map(x => x.trim()).filter(Boolean);
  const keywords = ['今日','支付','成交','订单','退款','曝光','点击','体验分','保证金','账户资金','发货','售后','工单','违规','风险','排行','较昨日','待处理','异常包裹'];
  const relevantLines = lines.filter(line => keywords.some(k => line.includes(k))).slice(0, 220);
  const cards = [...document.querySelectorAll('[data-metric], .metric-card, .stat-card, .index-card, .card, [class*=Card], [class*=card], [class*=metric], [class*=Metric]')]
    .filter(visible)
    .slice(0, 100)
    .map(el => clean(el.innerText))
    .filter(Boolean)
    .filter((v, i, a) => a.indexOf(v) === i)
    .slice(0, 60);
  const tables = [...document.querySelectorAll('table')].filter(visible).slice(0, 5).map(table => {
    const rows = [...table.querySelectorAll('tr')].slice(0, 20).map(row => [...row.querySelectorAll('th,td')].map(cell => clean(cell.innerText)));
    return rows;
  });
  return {title: document.title, url: location.href, relevantLines, cards, tables};
})()
"""

async def connect(profile: dict):
    port = int(profile['cdp_port'])
    pw = await async_playwright().start()

    async def _connect():
        return await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{port}')

    try:
        browser = await async_retry(_connect, attempts=4, base_delay=0.5)
    except Exception:
        await pw.stop()
        raise
    return pw, browser

async def get_page(browser, profile: dict):
    pages = []
    for ctx in browser.contexts:
        pages.extend(ctx.pages)
    if not pages:
        raise RuntimeError('No pages found via CDP')

    platform = profile.get('platform', '')
    cfg = load_platform_config(platform) if platform else {}
    target_host = profile.get('target_host') or cfg.get('target_host')
    preferred_paths = profile.get('preferred_paths') or cfg.get('preferred_paths') or []

    if target_host:
        for path in preferred_paths:
            for p in pages:
                if target_host in p.url and path in p.url:
                    return p
        for p in pages:
            if target_host in p.url:
                return p
    for p in pages:
        if p.url and p.url != 'about:blank':
            return p
    return pages[0]

async def action_status(profile_name: str):
    profile = load_profile(profile_name)
    pw, browser = await connect(profile)
    try:
        pages = []
        for ctx in browser.contexts:
            for p in ctx.pages:
                pages.append({'url': p.url, 'title': await p.title()})
        compact_print({'profile': profile_name, 'cdp': f"http://127.0.0.1:{profile['cdp_port']}", 'pages': pages})
    finally:
        await browser.close()
        await pw.stop()

async def action_eval(profile_name: str, js_file: str | None, js_inline: str | None):
    profile = load_profile(profile_name)
    pw, browser = await connect(profile)
    try:
        page = await get_page(browser, profile)
        js = Path(js_file).read_text(encoding='utf-8') if js_file else js_inline
        result = await page.evaluate(js)
        compact_print(result)
    finally:
        await browser.close()
        await pw.stop()

async def action_map(profile_name: str):
    await action_eval(profile_name, None, PAGE_MAP_JS)

async def action_dashboard(profile_name: str):
    profile = load_profile(profile_name)
    pw, browser = await connect(profile)
    try:
        page = await get_page(browser, profile)
        result = await page.evaluate(DASHBOARD_JS)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f'{profile_name}-dashboard-snapshot.json'
        atomic_write_json(out, result)
        compact_print({'saved': str(out), 'snapshot': result})
    finally:
        await browser.close()
        await pw.stop()

async def main():
    parser = argparse.ArgumentParser(description='Low-token CDP harness for CloakBrowser profiles')
    parser.add_argument('action', choices=['status','map','dashboard','eval'])
    parser.add_argument('--profile', default='doudian')
    parser.add_argument('--js-file')
    parser.add_argument('--js')
    args = parser.parse_args()
    if args.action == 'status':
        await action_status(args.profile)
    elif args.action == 'map':
        await action_map(args.profile)
    elif args.action == 'dashboard':
        await action_dashboard(args.profile)
    elif args.action == 'eval':
        if not args.js_file and not args.js:
            raise SystemExit('eval requires --js-file or --js')
        await action_eval(args.profile, args.js_file, args.js)

if __name__ == '__main__':
    asyncio.run(main())
