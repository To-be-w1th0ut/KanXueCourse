from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '客户端价格 / 数量信任',
    '优惠券与折扣逻辑',
    '回调与对账逻辑',
]

LABS = [
    {
        'domain': 'payment',
        'slug': 'client-total',
        'title': 'L01 客户端总价篡改',
        'subtitle': '服务端如果直接相信前端提交的 total，价格就等于交给用户自己填。',
        'difficulty': '基础',
        'story': '订单确认页为了适配前端活动价，直接接收客户端 total 字段。',
        'endpoint': '/labs/payment/client-total',
        'primary_class': '客户端价格 / 数量信任',
        'secondary_class': '客户端 total 字段',
        'timing_class': '提交订单时触发',
        'defense_focus': '服务端重算金额',
        'teacher_path': '第一关先讲“支付逻辑漏洞不一定需要注入，信任边界错了就够了”。',
        'hints': [
            '先区分谁在算价格：浏览器还是服务端。',
            '如果 total 直接来自客户端，价格边界就已经失守。',
            '安全模式应完全忽略客户端 total，按服务端商品单价重算。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh payment-orders 重置支付订单。',
    },
    {
        'domain': 'payment',
        'slug': 'negative-quantity',
        'title': 'L02 负数数量与余额反向增加',
        'subtitle': '数量和金额的符号校验缺失，可能把扣款逻辑变成充值逻辑。',
        'difficulty': '进阶',
        'story': '点券购买器允许输入数量，后端直接做 balance -= quantity * price。',
        'endpoint': '/labs/payment/negative-quantity',
        'primary_class': '客户端价格 / 数量信任',
        'secondary_class': '负数 / 符号校验缺失',
        'timing_class': '提交购买时触发',
        'defense_focus': '数量范围校验 / 服务端业务规则',
        'teacher_path': '这关适合引出“支付逻辑漏洞的核心常常是状态机和约束失效”。',
        'hints': [
            '看数量字段是否限制为正整数。',
            '如果扣款公式没有先验证语义，负数可能让结果反向。',
            '安全模式要先验证数量，再做余额变更。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh payment-wallet 重置钱包余额。',
    },
    {
        'domain': 'payment',
        'slug': 'coupon-reuse',
        'title': 'L03 优惠券重复使用',
        'subtitle': '优惠券验证通过后如果不正确消耗，就会被无限复用。',
        'difficulty': '进阶',
        'story': '一次性优惠券在 UI 上会变灰，但服务端没有真正扣减使用次数。',
        'endpoint': '/labs/payment/coupon-reuse',
        'primary_class': '优惠券与折扣逻辑',
        'secondary_class': '一次性券未正确消耗',
        'timing_class': '提交订单时触发',
        'defense_focus': '服务端扣减 / 原子更新 / 幂等消费',
        'teacher_path': '这关适合讲“客户端表现”和“服务端真实状态”是两件事。',
        'hints': [
            '先看优惠券是否真的在服务端减少次数。',
            '如果只是校验“还有效”，却不消耗状态，就能重复用。',
            '安全模式必须在同一事务里完成校验和扣减。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh payment-coupons 重置优惠券。',
    },
    {
        'domain': 'payment',
        'slug': 'duplicate-callback',
        'title': 'L04 重复支付回调',
        'subtitle': '回调不是只会来一次，不做幂等就会重复记账。',
        'difficulty': '高级',
        'story': '支付网关回调处理器每收到一次 success 都给用户加一次点券。',
        'endpoint': '/labs/payment/duplicate-callback',
        'primary_class': '回调与对账逻辑',
        'secondary_class': '缺少幂等处理',
        'timing_class': '回调到达时触发',
        'defense_focus': '订单状态机 / 回调幂等键',
        'teacher_path': '用它讲清“支付逻辑的安全边界不只在下单，还在异步通知和对账”。',
        'hints': [
            '先确认订单是否记录“已经处理过回调”。',
            '如果每个 success 都直接记账，就会被重复利用。',
            '安全模式要基于订单状态或回调幂等键去重。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh payment 重置支付状态。',
    },
]

LAB_INDEX = {item['slug']: item for item in LABS}

def get_lab(slug: str):
    return LAB_INDEX[slug]

def build_taxonomy():
    grouped = defaultdict(list)
    for item in LABS:
        grouped[item['primary_class']].append(item)
    return [{'name': name, 'labs': grouped[name]} for name in GROUP_ORDER if grouped[name]]
