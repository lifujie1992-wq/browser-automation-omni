from scripts.function_map_builder import build_function_map, classify_node


def test_classify_money_navigation():
    node = {'tag': 'a', 'text': '千川推广', 'href': '/ffa/ad/promotion-v2', 'selector': 'a:text("千川推广")'}
    kind, risk, flags = classify_node(node)
    assert kind == 'navigation'
    assert risk == 'medium'
    assert 'money_related' in flags


def test_classify_high_risk_inventory():
    node = {'tag': 'a', 'text': '库存管理', 'href': '/ffa/g/stock-manage/list', 'selector': 'a:text("库存管理")'}
    kind, risk, flags = classify_node(node)
    assert kind == 'navigation'
    assert risk == 'high'
    assert 'human_confirm_required' in flags


def test_build_function_map_summary_and_dedupe():
    raw = {
        'title': '首页',
        'url': 'https://fxg.jinritemai.com/ffa/mshop/homepage/index',
        'nodes': [
            {'tag': 'a', 'text': '商品创建', 'href': '/ffa/g/create', 'selector': 'a:text("商品创建")'},
            {'tag': 'a', 'text': '商品创建', 'href': '/ffa/g/create', 'selector': 'a:text("商品创建")'},
            {'tag': 'a', 'text': '库存管理', 'href': '/ffa/g/stock-manage/list', 'selector': 'a:text("库存管理")'},
        ],
    }
    fm = build_function_map(raw, 'doudian')
    assert fm['summary']['total_entrances'] == 2
    assert fm['summary']['high_risk_count'] == 1
    assert any(e['name'] == '商品创建' for e in fm['entrances'])
