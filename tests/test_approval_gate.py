from scripts.approval_gate import detect_risk


def profile_policy():
    return {
        'risk_policy': {
            'human_confirm_required': [
                'submit', 'publish', 'delete', 'price_change', 'inventory_change',
                'budget_change', 'bid_change', 'authorization', 'payment'
            ]
        }
    }


def test_detect_publish_risk():
    hits = detect_risk('click_publish', '立即发布', profile_policy())
    assert 'publish' in hits


def test_read_dashboard_is_safe():
    assert detect_risk('read_dashboard', '首页经营数据', profile_policy()) == []


def test_detect_budget_and_bid_risk():
    hits = detect_risk('update_campaign', '修改预算和出价', profile_policy())
    assert 'budget_change' in hits
    assert 'bid_change' in hits
