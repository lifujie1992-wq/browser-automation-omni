from extractors.doudian_home_metrics import as_num, parse_cards


def test_as_num_handles_money_percent_and_wan():
    assert as_num('¥1,437.4') == 1437.4
    assert as_num('1.5万') == 15000
    assert as_num('6.36%') == '6.36%'
    assert as_num('-') == '-'


def test_parse_cards_extracts_core_doudian_metrics():
    cards = [
        '用户支付金额 0 较昨日 持平 成交金额¥0',
        '成交订单数 0 较昨日 持平 同行基准值0',
        '商品曝光人数 991 构成 较昨日 71.51% 去分析全店流量',
        '商品点击人数 63 较昨日 72.00% 同行基准值404',
        '投放消耗 ¥0.76 较昨日 73.61% 同行基准值¥61.57',
        '搜索数据概览 近7天 搜索用户支付金额 ¥1,437.4 较上周期 26.76% 占比本店 39.38% 同行标杆 ¥4,868.24 搜索曝光人数 1.5万 较上周期 17.47% 同行标杆 5.34万',
        '黑色草莓bingbing 商家体验分 69 分 较昨日 持平 详情 商品 76 分 物流 73 分 服务 60 分 店铺资金 基础保证金 ￥500 体验保证金(可提现) ￥200 账户资金 ￥3538.47',
        'TOP退款原因 原因分析 退款金额 商品与描述信息不符 ¥435.2(33%) 商品缺货 ¥178.2(13%) 缺少用户权益 ¥158.7(12%)',
    ]
    metrics = parse_cards(cards)
    assert metrics['today']['user_pay_amount'] == 0
    assert metrics['today']['order_count'] == 0
    assert metrics['today']['product_exposure_users'] == 991
    assert metrics['today']['product_click_users'] == 63
    assert metrics['today']['ad_spend'] == 0.76
    assert metrics['search_7d']['search_pay_amount'] == 1437.4
    assert metrics['search_7d']['search_exposure_users'] == 15000
    assert metrics['experience']['merchant_experience_score'] == 69
    assert metrics['funds']['account_balance'] == 3538.47
    assert metrics['refund']['top_reasons'][0]['reason'] == '商品与描述信息不符'
