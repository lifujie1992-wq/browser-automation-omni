# BYOB Current Chrome Backend Integration

BYOB is the browser-automation-omni backend for the user's already-open normal Chrome session.
It is not a replacement for CloakBrowser/CDP in shop/admin automation. It fills a different slot:
use normal Chrome when the task depends on the user's current tab, everyday login state, extensions,
or an already-open browser page that should not be relaunched with a CDP port.

## Role in the stack

```text
CloakBrowser/CDP      = automation-owned trusted profile for commerce/admin workflows
BYOB/current Chrome   = user's real already-open Chrome session
CuaDriver             = native/visual/system UI and verification
browser-use/scout     = bounded unknown-page diagnosis
approval_gate         = blocks high-risk actions
```

## Use BYOB when

- The user says: "my Chrome", "current tab", "already open", "normal browser", "this page".
- The target login exists only in normal Chrome.
- Restarting Chrome or adding `--remote-debugging-port` would disrupt the user.
- The task needs the user's normal extensions, cookies, history, or active browsing context.
- BYOB tools can solve it with read/click/type/screenshot/table extraction/tab switching.
- Cross-origin iframe access is easier through BYOB `framePath` support.

## Do not default to BYOB when

- The task is a shop/admin/backend automation flow with a known CloakBrowser profile.
- The task needs strict account/shop isolation or anti-fraud browser identity.
- The action is publish/delete/payment/authorization/price/inventory/budget/bid without explicit approval.
- A fixed CDP endpoint already exists for the intended automation profile.

## Local installation placeholders

```text
Repo: ${BYOB_REPO:-$HOME/byob}
Doctor command: bun run doctor
Native bridge host: ${BYOB_HOME:-$HOME/.byob}/bridge-host.sh
Bridge sockets: ${BYOB_HOME:-$HOME/.byob}/bridges/*.sock
Chrome Native Messaging manifest: $HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/ai.byob.bridge.json
```

## Startup / readiness check

From the BYOB repo:

```bash
cd "${BYOB_REPO:-$HOME/byob}"
bun run doctor
```

Expected readiness signs:

- Chrome Native Messaging manifest exists.
- Extension is installed/enabled in normal Chrome.
- Bridge socket exists after Chrome + extension are active.
- MCP exposes browser tools such as `browser_list_tabs`, `browser_read`, `browser_click`, `browser_type`, `browser_screenshot`.

Do not kill or restart normal Chrome casually. If BYOB is not ready, report the missing prerequisite and ask the human to open/enable the extension or Chrome session.

## Runtime routing rule

For actual runtime use, call the router first:

```bash
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "帮我看下当前 Chrome 这个标签页"
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "读取这个商家后台的经营看板" --platform taobao
```

Router output fields:

```text
backend: cloakbrowser_cdp | byob | cuadriver | browser_use_scout
confidence: routing confidence
requires_approval: whether approval_gate/human confirmation is required
reasons: matched routing signals
next_step: recommended next operation
```

Rule order:

```text
if user mentions normal Chrome/current tab/already-open page:
    use BYOB first
elif task is commerce/admin and known profile exists:
    use CloakBrowser + CDP harness first
elif CDP/BYOB cannot see or operate visible UI:
    use CuaDriver
elif page is unknown or selectors drift:
    use browser-use/scout for diagnosis only
```

## Safety

BYOB controls the user's personal Chrome. Treat it as more sensitive than a disposable automation profile:

- Prefer read-only actions unless the user requests a specific operation.
- Stop for login, password, captcha, SMS/2FA, payment, authorization, publish, delete, price/inventory/budget/bid changes.
- Use approval_gate for high-risk write actions.
- Never run arbitrary `browser_eval` unless explicitly needed and enabled by configuration. Prefer specific BYOB tools first.

## Practical examples

Use BYOB:

```text
"看下我当前 Chrome 这个页面是什么"
"在我已经打开的标签页里提取这个表格"
"用我普通 Chrome 登录态查一下这个页面"
```

Use CloakBrowser/CDP instead:

```text
"打开某个商家后台"
"商品发布页填字段"
"店铺后台查询订单"
```

Use CuaDriver after BYOB/CDP:

```text
"弹出了系统文件选择器"
"页面上这个图表 DOM 里读不到"
"按钮可见但 CDP 点击没反应"
```
