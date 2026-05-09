# Browser Omni Runtime

独立运行目录，用于把 browser-automation-omni 做成通用、强力、可验证的浏览器操作运行时。

路径：
${BROWSER_OMNI_RUNTIME}

目标：
- 操作任意已登录浏览器环境，而不是绑定某个具体网站。
- 先低 token 读页面入口、表单、查询条件、表格、看板。
- 自动选择 CloakBrowser/CDP、BYOB/current Chrome、CuaDriver、browser-use scout。
- 登录/扫码/验证码停下让人协助。
- 发布、提交、删除、付款、授权、改价、库存、预算、出价等高风险动作必须 approval_gate。

核心组件：

1. contexts/registry.json
   记录平台、profile、CDP 端口、风险策略。示例 profile 可替换，不代表 runtime 只服务某个平台。

2. scripts/backend_router.py
   根据任务描述、platform、context 自动选择后端：cloakbrowser_cdp / byob / cuadriver / browser_use_scout，并标记是否需要 approval_gate。

3. scripts/launch_profile.py
   用 CloakBrowser 启动任意持久化 profile，并固定 CDP 端口。

4. scripts/cdp_harness.py
   通过 CDP 连接目标 profile，做低 token DOM/表单/表格/看板抽取。

5. scripts/function_map_builder.py
   把低 token map 结果去重、分类、风险标记，并写入 schema cache。

6. scripts/approval_gate.py
   写入审计日志，并拦截发布、提交、删除、改价、库存、预算、出价、授权、付款等高风险动作。

7. scripts/profile_lock.py
   管理 profile lock，避免多个任务并发操作同一浏览器 profile。

8. scripts/read_dashboard_safe.py
   安全读取看板：优先 CDP/DOM；如果 CDP 失败，明确输出 CuaDriver + vision 兜底策略。

9. extractors/*
   站点/页面专用解析器。当前仓库里的 doudian 相关文件只是示例适配器，不是 runtime 的默认目标。

通用后端路由：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "帮我看下当前 Chrome 这个标签页"
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "读取这个商家后台的经营看板" --platform taobao
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/backend_router.py "系统文件选择器弹出来了，DOM 看不到"

输出字段：backend、confidence、requires_approval、reasons、next_step。

通用 profile 操作：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/launch_profile.py --profile <profile>
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py status --profile <profile>
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/cdp_harness.py map --profile <profile>
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/function_map_builder.py --profile <profile>
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/read_dashboard_safe.py --profile <profile>

高风险动作审批：

# 只读动作会直接通过并记录 audit
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/approval_gate.py --profile <profile> --action read_dashboard --target dashboard --mode read --result ok

# 写操作会被拦截，除非显式带 --confirmed-by-human
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/approval_gate.py --profile <profile> --action publish --target final_submit --mode write --before draft --after published --result planned

审计日志：
${BROWSER_OMNI_RUNTIME}/logs/audit/YYYY-MM-DD.jsonl

Profile lock：

${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py status --profile <profile>
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py acquire --profile <profile> --owner task-name
${CLOAKBROWSER_PY} ${BROWSER_OMNI_RUNTIME}/scripts/profile_lock.py release --profile <profile> --owner task-name

后端选择原则：

- 普通网页/商家后台/登录态 profile：默认 CloakBrowser + CDP。
- 用户说“我的 Chrome / 当前标签页 / 已经打开的页面 / 普通浏览器登录态”：优先 BYOB/current Chrome。
- CDP/BYOB 不通、DOM 看不到 canvas/chart/native dialog、页面出现未知弹窗、或需要视觉核对：用 CuaDriver screenshot/window state + vision。
- 选择器失效、页面改版、未知流程：用 browser-use scout 诊断，不做生产执行。
- 任何发布、删除、付款、改价、改库存、改预算/出价等动作仍必须走 approval_gate。

BYOB readiness：
- 在 BYOB repo 内运行 `bun run doctor`。
- 不要为了 BYOB 随便 kill/restart 用户普通 Chrome；缺扩展、socket 或 manifest 时，让用户打开/启用对应 Chrome 扩展。

注意：
- 登录/扫码/验证码必须人类协助。
- 这个 runtime 不放在任何业务项目目录里。
- 不要随便 kill 浏览器；只操作明确记录的本项目 PID。
