# Browser Automation Omni

通用浏览器操作基座。

它不是某个平台的业务脚本，也不是售后、投流、商品发布这些垂直流程本身。它负责把“浏览器里能看到、能点、能填、能查、能导出”的能力抽成稳定底座，供后续垂直 skill 复用。

## 定位

Browser Automation Omni 只管浏览器操作层：

- 打开或接管浏览器
- 复用登录态
- 选择操作后端
- 低 token 读取页面
- 找入口、按钮、表单、筛选项、表格、看板
- 点击、输入、选择、上传、下载、导出
- 处理 iframe、弹窗、原生文件选择器
- 截图/视觉验证
- 高风险动作审批拦截
- 输出结构化数据、文件路径、页面状态证据

它不管业务决策：

- 售后规则
- 退款/退货判断
- 投流 ROI/ROAS 策略
- 出价/预算优化逻辑
- 商品标题/类目/属性策略
- 财务、CRM、ERP 等业务语义

这些应该放进单独的垂直 skill。

## 架构

```text
Vertical Skills
  ├─ doudian-aftersale-query
  ├─ ad-optimization-skill
  ├─ product-publish-skill
  └─ report-export-skill
          │
          ▼
Browser Automation Omni
  ├─ backend_router
  ├─ CloakBrowser/CDP
  ├─ BYOB/current Chrome
  ├─ CuaDriver
  ├─ browser-use scout
  ├─ approval_gate
  └─ profile_lock
```

## 后端选择

| 场景 | 默认后端 |
|---|---|
| 自动化专用登录态、风控敏感后台 | CloakBrowser + CDP |
| 用户已打开的普通 Chrome / 当前标签页 | BYOB/current Chrome |
| DOM/CDP 读不到、原生弹窗、文件选择器、视觉验证 | CuaDriver |
| 未知页面、选择器失效、页面改版 | browser-use scout |
| 发布、删除、付款、授权、改价、库存、预算、出价 | approval_gate 必须拦截 |

## 能力矩阵

```text
打开自动化 profile        -> CloakBrowser/CDP
接管普通 Chrome 当前页     -> BYOB/current Chrome
读取页面入口/按钮/表单      -> CDP/BYOB minimal DOM
填表/查询/筛选             -> CDP/BYOB handlers
表格/卡片/看板提取          -> CDP/BYOB，必要时 CuaDriver/vision
下载/导出报表              -> CDP/BYOB，原生保存弹窗用 CuaDriver
上传文件/素材              -> CDP file input，原生文件选择器用 CuaDriver
iframe/modal              -> CDP/BYOB frame tools，失败用 CuaDriver
未知页面/选择器漂移         -> browser-use scout 只诊断
高风险写动作               -> approval_gate mandatory
```

## 快速使用

### 1. 自动选择后端

```bash
export BROWSER_OMNI_RUNTIME=/Users/lifujie/browser-omni-runtime
export CLOAKBROWSER_PY=/Users/lifujie/github-tools/CloakBrowser/.venv/bin/python

$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/backend_router.py "帮我看下当前 Chrome 这个标签页"
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/backend_router.py "读取这个商家后台的经营看板" --platform generic_shop_admin
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/backend_router.py "系统文件选择器弹出来了，DOM 看不到"
```

输出：

```json
{
  "backend": "byob | cloakbrowser_cdp | cuadriver | browser_use_scout",
  "confidence": 0.88,
  "requires_approval": false,
  "reasons": ["current_chrome"],
  "next_step": "..."
}
```

### 2. 启动/检查 profile

```bash
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/launch_profile.py --profile generic_shop_admin
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/cdp_harness.py status --profile generic_shop_admin
```

### 3. 读取页面功能地图

```bash
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/cdp_harness.py map --profile generic_shop_admin
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/function_map_builder.py --profile generic_shop_admin
```

### 4. 安全读取看板/报表

```bash
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/read_dashboard_safe.py --profile generic_shop_admin
```

### 5. 高风险动作审批

只读动作：

```bash
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/approval_gate.py \
  --profile generic_shop_admin \
  --action read_dashboard \
  --target dashboard \
  --mode read \
  --result ok
```

写动作默认拦截：

```bash
$CLOAKBROWSER_PY $BROWSER_OMNI_RUNTIME/scripts/approval_gate.py \
  --profile generic_shop_admin \
  --action publish \
  --target final_submit \
  --mode write \
  --before draft \
  --after published \
  --result planned
```

## 垂直 skill 接入契约

垂直 skill 应声明：

```yaml
base_skill: browser-automation-omni
business_domain: <aftersale | ads | product_publish | report_export | crm | erp | finance | other>
required_context:
  platform: <site/platform>
  profile: <browser profile or current Chrome requirement>
  login_state: <required/optional>
entrypoints:
  - human_name: <入口名称>
    route_hint: <menu/search/url/filter path>
queries:
  - name: <query name>
    fields: [<keyword/date/status/...>]
outputs:
  - type: <json/table/csv/xlsx/screenshot>
    schema: <fields or path convention>
high_risk_actions:
  - <publish/delete/payment/authorize/price/inventory/budget/bid/...>
verification:
  - <readback/table count/toast/download exists/screenshot/...>
```

调用流程：

```text
1. 加载 browser-automation-omni
2. 加载垂直 skill
3. 垂直 skill 说明业务目标和页面上下文
4. 基座选择后端并执行浏览器操作
5. 基座返回结构化数据/文件路径/页面证据
6. 垂直 skill 应用业务规则
7. 高风险写动作走 approval_gate
8. 基座做执行后验证
```

## 目录

```text
browser_omni_runtime/
  common/
    backend_router.py
    config.py
    io.py
    retry.py
configs/
  generic_shop_admin.json
contexts/
  registry.json
docs/skill/
  browser-automation-omni-SKILL.md
  vertical-skill-contract.md
scripts/
  backend_router.py
  launch_profile.py
  cdp_harness.py
  function_map_builder.py
  read_dashboard_safe.py
  approval_gate.py
  profile_lock.py
extractors/
  *.py
tests/
  test_*.py
```

## 安全原则

- 不要随便 kill 浏览器，只操作明确记录的本项目 PID/profile。
- 登录、扫码、验证码、密码、2FA 必须人类协助。
- 不要把视觉猜测直接用于高风险写操作。
- 不要把业务规则塞进基座。
- 推送公开仓库前扫描 token、cookie、邮箱、绝对 profile 路径、本地隐私路径。

## 当前状态

评分：9.4/10

已具备：

- 通用基座定位
- 后端自动路由
- CloakBrowser/CDP 执行层
- BYOB/current Chrome 接管层
- CuaDriver 视觉/原生 UI 兜底策略
- browser-use scout 诊断层
- approval_gate 风险拦截
- 垂直 skill 接入契约
- 测试和敏感扫描流程

还可继续增强：

- 把示例适配器移动到 `examples/`
- 增加真实端到端 demo
- 增加更多 profile 模板
- 增加下载文件完整性校验
