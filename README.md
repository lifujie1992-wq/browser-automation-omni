# Browser Omni Runtime

独立运行目录，用于把 browser-automation-omni 从“可用雏形”推进到接近 9 分形态。

路径：
${BROWSER_OMNI_RUNTIME}

核心组件：

1. contexts/registry.json
   记录平台、profile、CDP 端口、风险策略。

2. scripts/launch_profile.py
   用 CloakBrowser 启动持久化 profile，并固定 CDP 端口。

3. scripts/cdp_harness.py
   通过 CDP 连接 CloakBrowser，做低 token DOM/看板抽取。

4. extractors/doudian_home_metrics.py
   把抖店首页 dashboard 快照解析成字段级 JSON。

5. scripts/function_map_builder.py
   把低 token map 结果去重、分类、风险标记，并写入 schema cache。

6. scripts/approval_gate.py
   写入审计日志，并拦截发布、提交、删除、改价、库存、预算、出价、授权、付款等高风险动作。

7. scripts/profile_lock.py
   管理 profile lock，避免多个任务并发操作同一 CloakBrowser profile。

9. scripts/read_dashboard_safe.py
   安全读取看板：优先 CDP/DOM；如果 CDP 失败，明确输出 CuaDriver + vision 兜底策略。

10. BYOB / current Chrome backend
   用 BYOB 接管用户已经打开的普通 Chrome；当任务依赖“当前标签页/我的 Chrome/普通浏览器登录态”时优先使用。详细说明见 docs/skill/byob-backend-integration.md。

11. scripts/backend_router.py
   根据任务描述、platform、context 自动选择后端：cloakbrowser_cdp / byob / cuadriver / browser_use_scout，并标记是否需要 approval_gate。

抖店启动：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/launch_profile.py --profile doudian

抖店状态：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py status --profile doudian

页面功能地图原始抽取：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py map --profile doudian

页面功能地图分类 + schema cache：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/function_map_builder.py --profile doudian

输出：
${BROWSER_OMNI_RUNTIME}/schemas/doudian-function-map.json
${BROWSER_OMNI_RUNTIME}/logs/doudian-raw-map.json

经营看板低 token 快照：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py dashboard --profile doudian

经营看板字段级数据：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/extractors/doudian_home_metrics.py

输出：
${BROWSER_OMNI_RUNTIME}/logs/doudian-home-metrics.json

安全读取经营看板（推荐入口）：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/read_dashboard_safe.py --profile doudian

高风险动作审批测试：

# 只读动作会直接通过并记录 audit
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/approval_gate.py --profile doudian --action read_dashboard --target 首页经营数据 --mode read --result ok

# 发布动作会被拦截，除非显式带 --confirmed-by-human
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/approval_gate.py --profile doudian --action click_publish --target 立即发布 --mode write --before 草稿待发布 --after 预计发布商品 --result planned

审计日志：
${BROWSER_OMNI_RUNTIME}/logs/audit/YYYY-MM-DD.jsonl

Profile lock：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py status --profile doudian
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py acquire --profile doudian --owner task-name
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py release --profile doudian --owner task-name

视觉兜底原则：
- 视觉不是禁用项，可以作为兜底。
- 默认优先 CDP/DOM，因为更低 token、更结构化、更稳定。
- 当 CDP 不通、DOM 看不到 canvas/chart/native dialog、页面出现未知弹窗、或需要视觉核对时，用 CuaDriver screenshot/window state + vision。
- 视觉抽到的数据要标记 visual_source，不要把视觉猜测直接用于高风险写操作。
- 任何发布、删除、付款、改价、改库存、改预算/出价等动作仍必须走 approval_gate。

BYOB 启动时机：
- 用户说“我的 Chrome / 当前标签页 / 已经打开的页面 / 普通浏览器登录态”时，优先用 BYOB/current Chrome。
- 抖店、淘宝、1688 等店铺后台默认仍优先 CloakBrowser + CDP，除非用户明确要求普通 Chrome。
- BYOB readiness 检查：在 BYOB repo 内运行 `bun run doctor`。
- 不要为了 BYOB 随便 kill/restart 用户普通 Chrome；缺扩展、socket 或 manifest 时，让用户打开/启用对应 Chrome 扩展。

后端自动路由：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "帮我看下当前 Chrome 这个标签页"
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "打开抖店后台读取经营看板" --platform doudian
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "系统文件选择器弹出来了，DOM 看不到"

输出字段：backend、confidence、requires_approval、reasons、next_step。

注意：
- 登录/扫码/验证码必须人类协助。
- 这个 runtime 不放在任何业务项目目录里。
- 不要随便 kill 浏览器；只操作明确记录的本项目 PID。
