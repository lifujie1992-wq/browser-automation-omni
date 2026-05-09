from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


COMMERCE_PLATFORMS = {
    'doudian', 'taobao', 'tmall', '1688', 'shein', 'temu', 'pinduoduo',
    'kuaishou', 'jd', 'shop', 'seller', 'admin', 'backend'
}

CURRENT_CHROME_TERMS = [
    'current chrome', 'my chrome', 'current tab', 'already open', 'normal chrome',
    '普通 chrome', '普通Chrome', '我的 chrome', '我的Chrome', '当前 chrome', '当前Chrome',
    '当前标签', '这个标签页', '已打开', '已经打开', '普通浏览器', '正常浏览器'
]

COMMERCE_TERMS = [
    '抖店', '淘宝', '天猫', '1688', 'temu', 'shein', '店铺后台', '商家后台',
    '卖家后台', '商品发布', '订单', '库存', '改价', '经营看板', '后台'
]

VISUAL_NATIVE_TERMS = [
    'native dialog', 'file picker', 'permission prompt', 'visual', 'screenshot',
    'DOM 看不到', 'dom 看不到', 'DOM点不到', 'dom点不到', '点不到', '弹窗',
    '系统文件', '文件选择器', '权限窗口', '原生', '截图', '视觉', 'canvas', '图表',
    '上传按钮', 'blocked ui'
]

SCOUT_TERMS = [
    'unknown', 'failure', 'diagnose', 'selector drift', 'redesign',
    '选择器失效', '失效', '页面改版', '诊断', '不知道', '未知', '失败原因', 'schema'
]

HIGH_RISK_TERMS = [
    'publish', 'submit', 'delete', 'payment', 'authorize', 'price', 'inventory',
    'budget', 'bid', '发布', '提交', '删除', '付款', '支付', '授权', '改价',
    '库存', '预算', '出价', '下架', '上架', '批量'
]


@dataclass(frozen=True)
class BackendDecision:
    backend: str
    confidence: float
    requires_approval: bool
    reasons: list[str]
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def choose_backend(task: str, platform: str | None = None, context: dict[str, Any] | None = None) -> BackendDecision:
    context = context or {}
    text = ' '.join(str(x) for x in [task, platform or '', context.get('url', ''), context.get('page_type', '')])
    reasons: list[str] = []

    current_chrome = _contains_any(text, CURRENT_CHROME_TERMS) or context.get('current_chrome') is True
    commerce_backend = (
        (platform or '').lower() in COMMERCE_PLATFORMS
        or _contains_any(text, COMMERCE_TERMS)
        or context.get('commerce_backend') is True
    )
    visual_native = _contains_any(text, VISUAL_NATIVE_TERMS) or context.get('visual_or_native_ui') is True
    scout_needed = _contains_any(text, SCOUT_TERMS) or context.get('selector_failure') is True
    high_risk = _contains_any(text, HIGH_RISK_TERMS) or context.get('high_risk_action') is True

    if current_chrome:
        reasons.append('current_chrome')
    if commerce_backend:
        reasons.append('commerce_backend')
    if visual_native:
        reasons.append('visual_or_native_ui')
    if scout_needed:
        reasons.append('unknown_or_failure_diagnosis')
    if high_risk:
        reasons.append('high_risk_action')

    if visual_native:
        backend = 'cuadriver'
        confidence = 0.9
        next_step = 'Use CuaDriver window state/screenshot/AX/mouse-keyboard, then recover structured state through CDP/BYOB when possible.'
    elif current_chrome and not commerce_backend:
        backend = 'byob'
        confidence = 0.88
        next_step = 'Use BYOB/current Chrome MCP tools against the active or selected normal Chrome tab.'
    elif commerce_backend:
        backend = 'cloakbrowser_cdp'
        confidence = 0.9
        next_step = 'Use CloakBrowser profile plus CDP harness; verify profile/shop before action.'
    elif scout_needed:
        backend = 'browser_use_scout'
        confidence = 0.78
        next_step = 'Use bounded scout for diagnosis/schema repair only; do not execute production writes.'
    else:
        backend = 'cloakbrowser_cdp'
        confidence = 0.62
        reasons.append('default_low_token_structured_control')
        next_step = 'Start with structured CDP/harness probing; escalate only if context indicates BYOB/CuaDriver/scout.'

    return BackendDecision(
        backend=backend,
        confidence=confidence,
        requires_approval=high_risk,
        reasons=reasons,
        next_step=next_step,
    )
