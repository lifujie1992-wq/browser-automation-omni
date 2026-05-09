# Browser Omni Runtime: 9-Point Optimization Notes

Session learning from turning the browser-automation-omni concept into a stronger local runtime on macOS.

## Goal

Move from a usable but screenshot-heavy flow toward a 9/10 browser automation stack:

```text
CloakBrowser persistent identity
  -> fixed CDP endpoint
  -> low-token CDP harness
  -> structured extractors / function maps
  -> human approval gates for risky actions
  -> audit logs
  -> browser-use only for unknown/failure diagnosis
```

## Runtime location

Keep runtime scaffolding outside business projects:

```text
${BROWSER_OMNI_RUNTIME}
```

Created structure:

```text
${BROWSER_OMNI_RUNTIME}/
├── README.md
├── contexts/registry.json
├── extractors/
├── logs/
├── schemas/
├── scripts/launch_profile.py
├── scripts/cdp_harness.py
└── state/
```

## Profile registry pattern

Use a registry so future tasks do not rediscover profile paths and ports:

```json
{
  "profiles": {
    "doudian": {
      "platform": "doudian",
      "display_name": "抖店后台",
      "target_url": "https://fxg.jinritemai.com/ffa/mshop/homepage/index",
      "profile_dir": "${CLOAKBROWSER_PROFILE_DIR}/doudian",
      "cdp_port": 9223,
      "locale": "zh-CN",
      "timezone": "Asia/Shanghai",
      "browser": "cloakbrowser",
      "source_repo": "${CLOAKBROWSER_REPO}",
      "venv_python": "${CLOAKBROWSER_PY}"
    }
  }
}
```

## CloakBrowser launcher pattern

Use `launch_persistent_context()` with a persistent profile and an explicit CDP port:

```python
ctx = launch_persistent_context(
    profile_dir,
    headless=False,
    humanize=True,
    viewport={"width": 1440, "height": 900},
    locale="zh-CN",
    timezone="Asia/Shanghai",
    args=[
        "--remote-debugging-port=9223",
        "--remote-allow-origins=*",
        "--window-size=1440,900",
    ],
)
```

Important: using a fixed CDP port is the key upgrade. Without it, the flow falls back to screenshot/vision more often.

Run:

```bash
${CLOAKBROWSER_PY} \
  ${BROWSER_OMNI_RUNTIME}/scripts/launch_profile.py --profile doudian
```

Expected readiness line:

```text
CloakBrowser ready profile=doudian title=首页 url=https://fxg.jinritemai.com/ffa/mshop/homepage/index cdp=http://127.0.0.1:9223
```

## CDP harness pattern

Connect to the fixed CDP endpoint with Playwright's `connect_over_cdp`:

```python
pw = await async_playwright().start()
browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9223")
```

Useful commands:

```bash
PY=${CLOAKBROWSER_PY}
HARNESS=${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py

$PY $HARNESS status --profile doudian
$PY $HARNESS map --profile doudian
$PY $HARNESS dashboard --profile doudian
$PY $HARNESS eval --profile doudian --js 'document.title'
```

## Low-token extraction lessons

1. Prefer CDP JS extraction over screenshots.
2. For first-pass page mapping, extract only title, URL, login hints, visible navigation/buttons/inputs/links.
3. For dashboards, extract relevant text lines, metric-like cards, and tables; save the raw snapshot for later parsing.
4. Use screenshots/vision only when DOM/CDP cannot see the data or for visual verification.

The dashboard snapshot was saved to:

```text
${BROWSER_OMNI_RUNTIME}/logs/doudian-dashboard-snapshot.json
```

## Observed doudian CDP outputs

`status` confirmed:

```json
{
  "profile": "doudian",
  "cdp": "http://127.0.0.1:9223",
  "pages": [
    {
      "url": "https://fxg.jinritemai.com/ffa/mshop/homepage/index",
      "title": "首页"
    }
  ]
}
```

`map` found useful entries such as:

- 订单管理
- 售后工作台
- 商品管理
- 评价管理
- 商家体验分
- 违规管理
- 店铺保障
- 商品素材
- 搜索运营
- 短视频运营
- AI智能成片
- 直播管理
- 图文运营
- 商城运营
- 推荐卡运营
- 活动广场
- 营销工具
- 优惠券
- 千川推广
- 联盟推广
- 发货中心
- 服务工单

`dashboard` extracted structured card text including:

- 用户支付金额 0
- 成交订单数 0
- 退款金额 0
- 商品曝光人数 991
- 商品点击人数 63
- 商品曝光-点击转化率 6.36%
- 支出金额 ¥0.76
- 投放消耗 ¥0.76
- 商家体验分 69 分
- 商品 76 分 / 物流 73 分 / 服务 60 分
- 基础保证金 ￥500
- 体验保证金(可提现) ￥200
- 账户资金 ￥3538.47

## Rating progression

Before fixed CDP harness:

```text
~6.5/10: CloakBrowser worked, but page reading still depended on CuaDriver screenshot/vision.
```

After this runtime:

```text
~8.2/10: persistent profile + fixed CDP + low-token harness + profile registry + dashboard snapshot.
```

To reach ~9/10, add:

1. Field-level `doudian_home_extractor.py` that parses dashboard text into stable JSON fields.
2. Function-map builder that deduplicates and classifies entrances as navigation/query/form/dashboard/high-risk.
3. Approval gate that blocks submit/publish/delete/price/inventory/budget/bid/authorization/payment until human confirms before/after.
4. Audit logger for profile, URL, action, selector, read/write, risk, confirmation, and result.
5. Schema cache for discovered pages and forms.
6. browser-use scout only for extractor failure, selector drift, unknown modal, or page redesign.

## 9-point supplement implemented on 2026-05-09

The local runtime now includes the main missing pieces for the ~9/10 target:

```text
${BROWSER_OMNI_RUNTIME}/extractors/doudian_home_metrics.py
${BROWSER_OMNI_RUNTIME}/scripts/function_map_builder.py
${BROWSER_OMNI_RUNTIME}/scripts/approval_gate.py
${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py
${BROWSER_OMNI_RUNTIME}/scripts/read_dashboard_safe.py
```

Validated outputs:

```text
${BROWSER_OMNI_RUNTIME}/logs/doudian-home-metrics.json
${BROWSER_OMNI_RUNTIME}/schemas/doudian-function-map.json
${BROWSER_OMNI_RUNTIME}/logs/audit/YYYY-MM-DD.jsonl
```

Key behavior:

1. `doudian_home_metrics.py` parses dashboard card text into stable fields such as `today.user_pay_amount`, `today.order_count`, `today.product_exposure_users`, `today.product_click_users`, `today.ad_spend`, `experience.merchant_experience_score`, `funds.account_balance`, and refund top reasons.
2. `function_map_builder.py` runs the CDP map, deduplicates entries, classifies them into dashboard/query/navigation/form/action/form_field/unknown, marks medium/high risk, and writes schema cache.
3. `approval_gate.py` records audit events and blocks high-risk actions like publish/delete/payment/price/inventory/budget/bid/authorization unless `--confirmed-by-human` is explicitly provided.
4. `profile_lock.py` provides profile-level lock status/acquire/release helpers to avoid concurrent operations on the same CloakBrowser profile.
5. `read_dashboard_safe.py` is the recommended dashboard read entrypoint: it tries CDP/DOM first, then emits an explicit CuaDriver + vision fallback note if CDP fails.

Vision policy clarification:

- Vision is allowed and useful as fallback; it is not forbidden.
- Prefer CDP/DOM for structured readable data because it is lower-token and more auditable.
- Use CuaDriver screenshot/window state + vision when CDP is unreachable, the data is canvas/chart/native-dialog-only, an unknown visual modal blocks operation, or visual verification is needed.
- Mark visually extracted fields as `visual_source` and never execute high-risk writes from visual guesses without `approval_gate` and human confirmation.

Commands:

```bash
PY=${CLOAKBROWSER_PY}
R=${BROWSER_OMNI_RUNTIME}

$PY $R/scripts/function_map_builder.py --profile doudian
$PY $R/extractors/doudian_home_metrics.py
$PY $R/scripts/read_dashboard_safe.py --profile doudian
$PY $R/scripts/approval_gate.py --profile doudian --action click_publish --target 立即发布 --mode write --before 草稿待发布 --after 预计发布商品 --result planned
$PY $R/scripts/profile_lock.py status --profile doudian
```

Expected approval behavior: the `click_publish` command exits with code 2 and `blocked_need_human_confirmation` unless `--confirmed-by-human` is supplied.
