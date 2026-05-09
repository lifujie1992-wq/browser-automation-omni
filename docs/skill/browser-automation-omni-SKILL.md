---
name: browser-automation-omni
description: Use when designing, building, debugging, or operating an all-purpose browser automation workflow that combines CloakBrowser identity/session isolation, browser harness/CDP precision control, and browser-use style AI exploration/diagnostics for e-commerce or complex web apps.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [browser-automation, cloakbrowser, browser-use, cdp, browser-harness, ecommerce, low-token]
    related_skills: [browser-automation-stack, systematic-debugging, spike]
---

# Browser Automation Omni

## Philosophy: A Good Tool for Humans

The goal is not to replace human judgment. The goal is to become a useful browser-work assistant that works the way humans naturally work:

1. Open a website in the user's real logged-in browser environment.
2. Observe what functions and entrances exist on the page.
3. Name those entrances in human language.
4. Let the user or policy decide which function matters.
5. Enter the selected function.
6. If it is a form workflow, understand fields with minimal DOM and fill them carefully.
7. If it is a query workflow, input keywords, date ranges, filters, status constraints, or other narrowing conditions.
8. If login, QR scan, password, 2FA, or other human-only authentication appears, stop and ask the human to assist.
9. After every meaningful action, read back the page state and verify the result.

This makes the automation feel like a competent assistant sitting beside the user: it can look, summarize, click, fill, query, and verify, but it should not hide important decisions or improvise high-risk changes.

## Overview

This skill defines the preferred "browser automation all-in-one" architecture for complex web workflows, especially e-commerce backends, listing publication, product data extraction, and multi-account operations.

The core idea is not to let one tool do everything. Use three layers with strict responsibility boundaries:

- **CloakBrowser**: trusted identity, browser fingerprint, login state, store/account isolation.
- **browser harness / CDP bridge**: deterministic, low-token, precise execution against the current browser tab.
- **browser-use / AI scout**: exploration, page understanding, schema drafting, and failure diagnosis only when the page is unknown or broken.

Default rule:

```text
CloakBrowser supplies identity.
browser harness executes 99% of actions.
browser-use scouts only on unknowns/failures.
```

This prevents high-token autonomous browsing from taking over stable production flows while still allowing AI to help when a page is unfamiliar, redesigned, or failing.

## When to Use

Use this skill when the task involves:

- Building a browser automation system that must reuse real logged-in sessions.
- Connecting automation to CloakBrowser profiles or anti-detect browser environments.
- Deciding whether to use browser-use, CDP, browser harness, Playwright, or CuaDriver.
- Designing low-token browser automation flows.
- Adapting a new e-commerce backend page.
- Reading dashboards, analytics pages, ad/投流 pages, CRM/admin panels, SaaS consoles, or finance/reporting pages.
- Extracting browser-only data and passing it to another model, rules engine, spreadsheet, database, or human decision workflow.
- Building a human-in-the-loop adjustment flow where AI suggests actions and a person approves ROI/budget/bid/creative changes.
- Diagnosing a broken selector, unknown modal, iframe, or new required field.
- Converting exploratory page understanding into reusable `context / data / schema / extractor / analyzer / handler / publisher` architecture.
- Avoiding accidental operations on real shop/admin systems.

Do **not** use browser-use as the main executor for stable, high-value flows such as publishing products, deleting data, authorizing apps, changing prices, paying, or submitting irreversible forms. Use deterministic harness actions with validation and explicit guardrails.

## Mental Model

```text
                    ┌──────────────────────┐
                    │   CloakBrowser        │
                    │ identity/session/env  │
                    └──────────┬───────────┘
                               │ current logged-in tab / CDP endpoint
                               ▼
                    ┌──────────────────────┐
                    │ browser harness/CDP   │
                    │ precise execution     │
                    └──────────┬───────────┘
                               │ minimal DOM snapshot / failure signal
                               ▼
                    ┌──────────────────────┐
                    │ CuaDriver             │
                    │ visual/system/native  │
                    └──────────┬───────────┘
                               │ visible-only or native state
                               ▼
                    ┌──────────────────────┐
                    │ browser-use / scout   │
                    │ explore + diagnose    │
                    └──────────────────────┘

                    Side backend:
                    BYOB/current Chrome is selected instead of CloakBrowser/CDP
                    when the target is the user's already-open normal Chrome session.
```

Map this to reusable browser automation architectures:

For form/action workflows:

```text
context   = CloakBrowser profile / shop / account / login state
data      = what to fill or extract
schema    = where each field lives on the page
handler   = how to interact with each field
publisher = in what order to execute and validate
```

For dashboard/analytics/投流 workflows:

```text
context   = platform/account/campaign/date range/login state
data      = extracted metrics and dimensions
schema    = where tables/cards/charts/filters live
extractor = how to read tables, APIs, cards, chart tooltips, downloads
analyzer  = rules engine, LLM, statistical model, or human review queue
handler   = deterministic adjustment actions, if approved
operator  = human-in-the-loop approval for budget/bid/ROI changes
```

## Dependency Bootstrap Rule

This skill assumes three core capabilities may be needed:

1. CloakBrowser for persistent identity/session/fingerprint.
2. browser harness / CDP bridge for low-token deterministic browser control.
3. BYOB/current Chrome for the user's already-open normal Chrome session when the task depends on current tab/login state.
4. browser-use for AI scouting, page exploration, and failure diagnosis.

Before running a real workflow, check whether these capabilities exist locally. If any are missing, install or recover them from their official GitHub/upstream source first. Do not silently substitute unrelated same-name packages, forks, random npm packages, or standard Playwright Chromium.

Preferred source-first procedure:

1. `git clone` the exact upstream repository into an isolated tools directory such as `${TOOLS_DIR}/<repo>`.
2. Read README and package metadata before installing.
3. Install in a scoped venv/project directory, not inside unrelated business repos.
4. Verify command/import/runtime provenance.
5. Record install path, profile path, process ID, and any fallback used.

Known bootstrap examples:

```bash
# CloakBrowser official source
mkdir -p ${TOOLS_DIR}
git clone https://github.com/CloakHQ/CloakBrowser ${CLOAKBROWSER_REPO}
cd ${CLOAKBROWSER_REPO}
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m cloakbrowser info
```

```bash
# browser-use isolated install when missing
mkdir -p ${BROWSER_USE_WORKSPACE}
python3 -m venv ${BROWSER_USE_WORKSPACE}/.venv
${BROWSER_USE_WORKSPACE}/.venv/bin/python -m pip install -U pip
${BROWSER_USE_WORKSPACE}/.venv/bin/python -m pip install browser-use
```

For browser harness/CDP bridge, first inspect the user's existing BYOB/browser-harness setup if present. If absent, use the exact upstream or project the user specifies; clone it, read its README, then install. Do not invent a bridge or use a visually opened browser as a substitute.

## Login and Human Assistance Rules

Persistent login is a first-class capability, not a convenience:

- Prefer CloakBrowser or the user's current logged-in browser profile.
- Do not open a fresh standard Playwright/Chromium browser when the task depends on trust, cookies, account state, or anti-fraud history.
- If the page asks for QR scan, username/password, SMS code, 2FA, captcha, device verification, or account selection that cannot be safely inferred, stop and ask the human to complete that step.
- After the human completes login/verification, continue from the same browser session and verify the landing page.
- Never ask the user to share passwords or SMS codes in chat unless they explicitly choose to; prefer having the user type/scan directly in the browser.

## Tool Responsibilities

### 1. CloakBrowser: identity layer

CloakBrowser owns:

- Browser fingerprint and environment.
- Platform/store/account separation.
- Login state, cookies, localStorage, sessionStorage.
- Profile-level proxy and anti-detect settings if configured.
- Human-established sessions for high-friction platforms.

Before opening a login-sensitive target, verify the intended identity browser is actually available and running. Do not silently fall back to standard Chrome just because it is open.

Mac checks:

```bash
mdfind 'kMDItemDisplayName == *Cloak* || kMDItemFSName == *Cloak*'
find /Applications ~/Applications -maxdepth 3 -iname '*cloak*' 2>/dev/null
ps aux | grep -i 'cloak' | grep -v grep || true
```

If CloakBrowser is not installed/running, stop and report that. Ask the human to install/open the correct profile, or explicitly approve a fallback browser. Label any fallback as non-CloakBrowser.

Store context records like:

```json
{
  "platform": "taobao",
  "shop_name": "Example Shop",
  "profile_name": "cloak-taobao-shop-a",
  "cdp_endpoint": "http://127.0.0.1:9222",
  "login_state": "verified",
  "schema_version": "taobao_publish_v3"
}
```

Never casually replace this with a fresh Playwright profile when login/session reuse matters.

### 2. browser harness / CDP bridge: execution layer

browser harness owns:

- Listing targets/tabs.
- Reading minimal DOM snapshots.
- Executing JavaScript.
- Clicking selectors.
- Typing into fields.
- Selecting dropdowns.
- Uploading files.
- Handling iframes.
- Validating toast/error/success states.
- Writing reproducible execution logs.

For a CDP Browser Bridge style HTTP API, typical calls are:

```bash
curl -s http://localhost:3456/health
curl -s http://localhost:3456/targets
curl -s -X POST "http://localhost:3456/eval?target=<TARGET_ID>" -d 'document.title'
curl -s -X POST "http://localhost:3456/click?target=<TARGET_ID>" -d '#submit'
```

Use minimal extraction instead of full page dumps:

```javascript
(() => {
  return [...document.querySelectorAll('[data-field], input, textarea, select, button')]
    .slice(0, 120)
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      id: el.id || '',
      name: el.getAttribute('name') || '',
      text: (el.innerText || el.value || el.placeholder || '').trim().slice(0, 80),
      required: el.required || el.getAttribute('data-required') === 'true',
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      aria: el.getAttribute('aria-label') || ''
    }))
})()
```

### 3. browser-use / AI scout: exploration and diagnosis layer

browser-use owns:

- Understanding an unfamiliar page.
- Producing a field/schema draft.
- Explaining why a flow failed.
- Finding changed buttons, new fields, unknown modals, or iframe boundaries.
- Suggesting handler fixes.

Keep tasks short and bounded:

```text
Analyze this minimal DOM snapshot. Return JSON with fields, selectors, required flags, handlers, risks, and validation hints. Do not execute final submit actions.
```

Good browser-use tasks:

- "Explore this product publish page and draft a schema."
- "Given this failure log and DOM snapshot, diagnose why submit failed."
- "Find the new selector for the publish button."
- "Identify whether this unknown overlay is a login modal, permission modal, or validation error."

Bad browser-use tasks:

- "Publish 100 products by yourself."
- "Click whatever is necessary until it works."
- "Delete invalid products."
- "Authorize this app."

### Backend Selection Router

Run the router before touching the browser:

```bash
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "帮我看下当前 Chrome 这个标签页"
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "打开抖店后台读取经营看板" --platform doudian
```

Router output:

```text
backend: cloakbrowser_cdp | byob | cuadriver | browser_use_scout
confidence: routing confidence
requires_approval: whether approval_gate/human confirmation is required
reasons: matched routing signals
next_step: recommended next operation
```

Routing priority:

1. Visual/native/dialog/DOM-invisible state -> `cuadriver`.
2. User's current normal Chrome/current tab -> `byob`.
3. Commerce/admin backend or known platform -> `cloakbrowser_cdp`.
4. Unknown page, selector drift, schema/failure diagnosis -> `browser_use_scout`.
5. Publish/delete/payment/authorization/price/inventory/budget/bid -> keep selected backend but set `requires_approval=true`.

## Page Exploration Pattern

Use the cheapest observation that answers the question. The assistant should discover a page like a human would, but with machine-readable, low-token probes.

### 1. First pass: page identity and top-level entrances

Extract only:

- title / URL
- navigation labels
- visible primary buttons
- search boxes
- filter controls
- table/card names
- modal/login state

Example minimal probe:

```javascript
(() => {
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  const text = el => (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 80)
  const nodes = [...document.querySelectorAll('a,button,input,textarea,select,[role=button],[role=tab],[role=menuitem]')]
    .filter(visible)
    .slice(0, 160)
    .map(el => ({
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      text: text(el),
      id: el.id || '',
      name: el.getAttribute('name') || '',
      type: el.getAttribute('type') || '',
      href: el.getAttribute('href') || ''
    }))
  return {title: document.title, url: location.href, nodes}
})()
```

### 2. Classify entrances

Classify visible functions into:

- navigation entrance
- form workflow
- query/search workflow
- dashboard/reporting workflow
- upload/material workflow
- settings/config workflow
- dangerous action workflow
- login/verification workflow

Return a compact function map:

```json
{
  "page": "seller_home",
  "entrances": [
    {"name": "订单管理", "type": "navigation", "selector": "...", "risk": "low"},
    {"name": "商品发布", "type": "form", "selector": "...", "risk": "high_submit"},
    {"name": "数据中心", "type": "dashboard", "selector": "...", "risk": "read_only"}
  ]
}
```

### 3. Deepen only the selected function

Do not map the whole site upfront. After the user chooses a function or the task identifies one, inspect only that area/page.

For forms, extract:

- labels
- required flags
- input/select/textarea selectors
- options
- validation text
- submit/save/draft buttons

For queries, extract:

- search inputs
- date pickers
- status filters
- dropdown options
- query/reset/export buttons
- result table columns

## Form and Query Patterns

### Form workflow

1. Extract minimal form schema.
2. Match data fields to labels/selectors.
3. Fill one field at a time.
4. Read back value or validation state.
5. Stop before final submit if the action is high-risk or irreversible.
6. Submit only after explicit permission or safe policy.

### Query workflow

1. Identify query inputs and filters.
2. Fill keyword/date/status constraints.
3. Click query/search.
4. Wait for result state change.
5. Extract result table/cards/download link.
6. Summarize or pass structured data to analyzer.

## Dashboard / 投流 / Analytics Workflows

This stack is especially strong for pages that cannot be accessed cleanly through public APIs because the data only exists behind logged-in browser sessions, anti-bot checks, dynamic tables, or internal SaaS dashboards.

Typical examples:

- Ad platform dashboards: ROI, ROAS, spend, impressions, CTR, CPC, CPA, GMV, conversion rate.
- E-commerce business intelligence pages: traffic sources, SKU performance, funnel metrics.
- CRM/admin panels: lead status, ticket queues, customer segments.
- Finance/reporting consoles: downloadable reports, reconciliations, statements.
- Competitor/research pages where login state and current browser context matter.

Preferred flow:

```text
CloakBrowser profile
  -> harness sets filters/date range/account/campaign
  -> harness extracts compact structured metrics
  -> analyzer/model computes recommendation
  -> human reviews recommendation and risk
  -> harness applies approved changes only
  -> harness validates and logs result
```

### Data extraction pattern

For tables/cards, do not screenshot first. Extract structured DOM where possible:

```javascript
(() => {
  const rows = [...document.querySelectorAll('table tbody tr')].slice(0, 200)
  return rows.map(row => [...row.querySelectorAll('th,td')].map(cell => cell.innerText.trim()))
})()
```

For dashboard cards:

```javascript
(() => {
  return [...document.querySelectorAll('[data-metric], .metric-card, .stat-card')]
    .slice(0, 80)
    .map(el => ({
      label: (el.querySelector('.label')?.innerText || el.getAttribute('data-metric') || '').trim(),
      value: (el.querySelector('.value')?.innerText || el.innerText || '').trim().slice(0, 120)
    }))
})()
```

If chart values are canvas-only or hidden behind hover tooltips, try in order:

1. Inspect network responses through CDP if available.
2. Query framework state or embedded JSON in the page.
3. Trigger tooltip events and read DOM tooltip text.
4. Use CuaDriver screenshot/vision only as fallback.

### Human-in-the-loop ROI adjustment

For ROI/budget/bid changes, separate recommendation from execution:

```json
{
  "campaign": "夏季拖鞋-搜索推广",
  "observed": {
    "spend": 320.5,
    "gmv": 1180.0,
    "roi": 3.68,
    "target_roi": 4.2,
    "conversions": 18
  },
  "recommendation": {
    "action": "decrease_bid",
    "amount_pct": 8,
    "reason": "ROI below target and spend is statistically meaningful",
    "risk": "medium"
  },
  "requires_human_approval": true
}
```

Execution rule:

- AI/model may recommend.
- Human or explicit policy must approve.
- Harness applies the exact approved change.
- Harness reads back the value and logs before/after.

### Model handoff pattern

When passing dashboard data to another model, send compact normalized JSON, not screenshots or raw DOM:

```json
{
  "platform": "ad-platform",
  "account": "shop-a",
  "date_range": "last_7_days",
  "metrics": [
    {"campaign": "A", "spend": 100, "gmv": 520, "roi": 5.2, "ctr": 0.034, "cpa": 12.5},
    {"campaign": "B", "spend": 220, "gmv": 610, "roi": 2.77, "ctr": 0.018, "cpa": 31.2}
  ],
  "question": "Recommend budget/bid adjustments under max daily budget 500. Return JSON only."
}
```

## Default Workflow

### A. New platform or new page adaptation

1. Open the target shop/admin page in CloakBrowser manually or via the known profile.
2. Confirm the correct profile/shop/account is active.
3. Use browser harness to extract a minimal DOM snapshot.
4. Give the minimal snapshot to browser-use / AI scout.
5. Generate a schema draft:
   - field name
   - label
   - selector candidate
   - required flag
   - handler type
   - options if select/radio
   - validation hint
   - iframe/modal risk
6. Manually review dangerous fields and final actions.
7. Convert the schema into deterministic harness handlers.
8. Run in dry-run mode.
9. Validate page state, error messages, and logs.
10. Only then enable real submit/publish.

### B. Stable daily execution

1. Load CloakBrowser context for the target shop/account.
2. Attach browser harness to the current tab or known CDP target.
3. Run publisher flow with deterministic handlers.
4. Validate after each high-risk step.
5. Emit compact logs:
   - field filled
   - selector used
   - value preview
   - validation result
   - screenshot path only if needed
6. Do not involve browser-use unless a failure or unknown state occurs.

### C. Failure diagnosis

When harness fails:

1. Capture the failure reason:
   - selector not found
   - click did nothing
   - validation error
   - unknown modal
   - iframe missing
2. Extract a small diagnostic DOM snapshot around the area.
3. Optionally capture a screenshot or CuaDriver window state if DOM is insufficient.
4. Ask browser-use / AI scout to diagnose, not to execute.
5. Patch schema or handler.
6. Re-run the failed step only.
7. Save the new selector/handler as durable code or skill knowledge if reusable.

## Low-Token Rules

Prefer this order:

1. Harness direct JS / selector query.
2. Harness small DOM snapshot.
3. CuaDriver AX tree or screenshot for non-DOM/native UI.
4. browser-use bounded scout task.
5. Full autonomous browser-use run only as a throwaway spike.

Token-saving patterns:

- Return only fields/buttons relevant to the current step.
- Slice long text to 80-200 chars.
- Limit DOM lists to the first N candidates.
- Filter by visible elements.
- Extract labels and selectors instead of full outerHTML.
- Pass failure logs plus a minimal snapshot to browser-use, not the whole page.
- Cache schema after exploration and reuse it.

Avoid:

- Dumping full DOM for large e-commerce pages.
- Sending repeated screenshots when text DOM is enough.
- Letting browser-use observe every stable step.
- Re-discovering fields that already exist in schema.

## Safety Rules

High-risk actions require deterministic control:

- Final publish/submit.
- Price changes.
- Inventory changes.
- Delete/remove/archive.
- Payment or order operations.
- OAuth/authorization grant.
- Bulk operations.

For high-risk actions:

1. Use harness selectors, not autonomous guessing.
2. Validate target account/shop before action.
3. Validate payload summary before action.
4. Prefer dry-run first.
5. Capture final confirmation state.
6. Log irreversible action details.

## Recommended Data Contracts

### Context

```json
{
  "platform": "doudian",
  "shop_name": "Example Shop",
  "profile_name": "cloak-doudian-shop-a",
  "target_url": "https://example.com/publish",
  "cdp_endpoint": "http://127.0.0.1:9222",
  "schema_version": "doudian_publish_v1"
}
```

### Schema

```json
{
  "page": "product_publish",
  "fields": [
    {
      "field": "title",
      "label": "商品标题",
      "selector": "input[name='title']",
      "required": true,
      "handler": "type_text",
      "validation": "non_empty; 10-60 chars"
    },
    {
      "field": "category",
      "label": "类目",
      "selector": "#category",
      "required": true,
      "handler": "select_option",
      "options": ["家居日用", "数码配件"]
    }
  ],
  "actions": {
    "save_draft": "button:has-text('保存草稿')",
    "publish": "button:has-text('发布商品')"
  }
}
```

### Execution Log

```json
{
  "step": "fill_title",
  "selector": "input[name='title']",
  "handler": "type_text",
  "value_preview": "便携式桌面收纳盒...",
  "ok": true,
  "validation": "field value readback matched"
}
```

### Failure Diagnosis Request

```json
{
  "failure": {
    "step": "click_publish",
    "error": "selector not found: button.publish"
  },
  "snapshot": {
    "buttons": ["保存草稿", "立即发布", "预览"],
    "modals": [],
    "iframes": ["publish-main"]
  },
  "ask": "Diagnose the likely cause and propose schema/handler fix. Do not execute."
}
```

## Implementation Pattern

A minimal implementation should have these modules:

```text
browser_automation_omni/
├── contexts/          # CloakBrowser profile/account/shop records
├── schemas/           # platform page schemas
├── handlers/          # deterministic field interactions
├── publishers/        # ordered flows
├── scouts/            # browser-use/LLM exploration + diagnosis
├── logs/              # compact execution logs
└── scripts/           # CLI entrypoints
```

Suggested interfaces:

```python
class ContextProvider:
    def get_context(platform: str, shop_name: str) -> BrowserContext: ...

class Harness:
    def list_targets(self) -> list[Target]: ...
    def eval(self, target_id: str, js: str) -> dict: ...
    def click(self, target_id: str, selector: str) -> None: ...
    def extract_minimal_snapshot(self, target_id: str) -> dict: ...

class Scout:
    def draft_schema(self, snapshot: dict) -> dict: ...
    def diagnose(self, failure: dict, snapshot: dict) -> dict: ...

class Publisher:
    def dry_run(self, data: dict) -> ValidationResult: ...
    def publish(self, data: dict, confirm: bool = False) -> PublishResult: ...
```

## CuaDriver / Vision Fallback

Vision is allowed and useful as a fallback; it is **not** forbidden. The preferred order is still:

```text
CDP/DOM structured extraction
  -> focused DOM/AX snapshot
  -> CuaDriver screenshot/window state + vision
  -> browser-use scout for unknown/failure diagnosis
```

Use CuaDriver and vision when:

- The app is native macOS UI.
- DOM/CDP cannot see the element.
- Browser harness is unavailable or the fixed CDP port is unreachable.
- A canvas/WebGL/chart/custom-rendered UI hides values from the DOM.
- A native dialog, login/verification UI, or unknown visual modal blocks the page.
- You need visual verification after a meaningful state change.
- You need window-level operations: close app, click native dialog, screenshot, AX tree.

Rules for visual fallback:

1. Prefer CDP/DOM for structured readable data because it is lower-token, more auditable, and easier to parse.
2. If CDP/DOM fails or misses visible information, use CuaDriver screenshot/window state + vision without treating that as a failure of the architecture.
3. Mark visually extracted fields as `visual_source` or include screenshot/window-state provenance in logs.
4. Do not execute high-risk writes from visual guesses alone. Publishing, deleting, payment, authorization, price/inventory/budget/bid changes must still pass the approval gate and human confirmation.
5. If vision reveals selector drift or a redesigned page, use it to repair schema/handlers, then return to deterministic CDP/harness execution.

CuaDriver is not the primary browser automation layer for DOM-heavy workflows. It is the fallback for native UI, visual/AX inspection, canvas-like data, and human-verifiable screenshots.

For the local 9-point browser automation runtime pattern (profile registry, fixed CloakBrowser CDP port, CDP harness commands, and remaining steps to reach ~9/10), see:

```text
references/browser-omni-runtime-9point.md
```

## CloakBrowser Recovery / Install Reference

For source-first recovery/install from `https://github.com/CloakHQ/CloakBrowser`, persistent profile launching, and macOS verification details, see:

```text
references/cloakbrowser-source-install-and-persistent-session.md
```

Key lesson: CloakBrowser may appear as a `Chromium` process from `${CLOAKBROWSER_HOME}/...`, not as `/Applications/CloakBrowser.app`. Verify by executable path and profile `user-data-dir`, not app display name alone.

## Demo Reference

A local throwaway demo was created at:

```text
${BROWSER_STACK_DEMO}
```

Run it with:

```bash
cd ${BROWSER_STACK_DEMO}
source .venv/bin/activate
python best_practice_demo.py
```

It demonstrates:

- CloakBrowser context record.
- Minimal DOM snapshot.
- Scout-generated schema.
- Harness execution log.
- Successful validation.
- Failure diagnosis when a required field is missing.

## Common Pitfalls

1. **Using browser-use as the production executor.**
   It is useful for exploration but expensive and less deterministic. Convert findings into harness schemas/handlers.

2. **Starting a fresh browser when login state matters.**
   Use CloakBrowser or the user's current browser/profile when platform trust and cookies matter.

3. **Dumping the entire DOM.**
   Large admin pages waste tokens and bury the useful details. Extract focused snapshots.

4. **Letting AI click final submit.**
   High-value actions must be deterministic, validated, and logged.

5. **Ignoring iframes and modals.**
   Many e-commerce uploaders and material selectors live in iframes or virtualized panels. Detect them explicitly.

6. **Mixing data, schema, handler, and publisher logic.**
   Keep the four layers separate so new platforms can be adapted without rewriting everything.

7. **Killing or cleaning browser processes broadly.**
   Only stop the specific profile/process you started. Do not kill the user's normal Chrome/CloakBrowser session casually.

8. **Not validating readback.**
   After filling, read the field value or page state back through harness before proceeding.

## Verification Checklist

Before calling a browser automation flow complete:

- [ ] Correct CloakBrowser profile/shop/account is active.
- [ ] The target tab/URL matches the intended platform page.
- [ ] The automation uses harness for stable execution.
- [ ] browser-use is bounded to exploration or diagnosis only.
- [ ] Minimal DOM snapshots are used instead of full dumps.
- [ ] Schema separates field selectors from execution code.
- [ ] Handlers are deterministic and reusable.
- [ ] Publisher flow has dry-run and validation steps.
- [ ] High-risk final actions are explicitly guarded.
- [ ] Execution logs include selectors, handlers, value previews, and validation results.
- [ ] Failures produce actionable diagnosis and schema/handler patches.
