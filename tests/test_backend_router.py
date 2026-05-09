from browser_omni_runtime.common.backend_router import choose_backend


def test_routes_current_chrome_request_to_byob():
    decision = choose_backend("帮我看下当前 Chrome 这个标签页的表格")

    assert decision.backend == "byob"
    assert decision.confidence >= 0.8
    assert "current_chrome" in decision.reasons


def test_routes_shop_backend_to_cloakbrowser_cdp():
    decision = choose_backend("打开商家后台，读取经营看板", platform="shop_admin")

    assert decision.backend == "cloakbrowser_cdp"
    assert decision.requires_approval is False
    assert "commerce_backend" in decision.reasons


def test_routes_visual_native_dialog_to_cuadriver():
    decision = choose_backend("页面弹出了系统文件选择器，DOM 点不到上传按钮")

    assert decision.backend == "cuadriver"
    assert "visual_or_native_ui" in decision.reasons


def test_routes_unknown_selector_failure_to_scout():
    decision = choose_backend("选择器失效了，页面改版，帮我诊断原因")

    assert decision.backend == "browser_use_scout"
    assert "unknown_or_failure_diagnosis" in decision.reasons


def test_high_risk_action_requires_approval_even_with_shop_backend():
    decision = choose_backend("在淘宝后台把这个商品改价并发布", platform="taobao")

    assert decision.backend == "cloakbrowser_cdp"
    assert decision.requires_approval is True
    assert "high_risk_action" in decision.reasons


def test_router_prefers_cuadriver_when_current_chrome_has_native_dialog():
    decision = choose_backend("我当前 Chrome 弹出权限窗口，网页 DOM 看不到")

    assert decision.backend == "cuadriver"
    assert "current_chrome" in decision.reasons
    assert "visual_or_native_ui" in decision.reasons
