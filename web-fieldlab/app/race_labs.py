from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '优惠券 / 限额竞争',
    '库存竞争',
    '余额竞争',
    '名额竞争',
]

LABS = [
    {
        'domain': 'race',
        'slug': 'coupon-burst',
        'title': 'L01 一次性优惠券竞争兑换',
        'subtitle': '先查剩余次数再扣减，如果不是原子操作，并发下就会多次成功。',
        'difficulty': '进阶',
        'story': '演示台提供“一键并发 10 次兑换”的按钮，方便课堂复现竞争窗口。',
        'endpoint': '/labs/race/coupon-burst',
        'primary_class': '优惠券 / 限额竞争',
        'secondary_class': 'check-then-update',
        'timing_class': '并发触发',
        'defense_focus': '锁 / 原子更新 / 事务',
        'teacher_path': '先讲竞态窗口，再通过并发按钮让学生直接看到 success_count 超出预期。',
        'hints': [
            '看逻辑是不是先查 remaining，再 sleep，再更新。',
            '如果多个请求在更新前都看到同一个剩余额度，就可能一起成功。',
            '安全模式常见修法是锁、事务或条件更新。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh race-coupons 重置竞态优惠券。',
    },
    {
        'domain': 'race',
        'slug': 'inventory-burst',
        'title': 'L02 单件库存超卖',
        'subtitle': '库存检查与扣减分离时，多个并发下单会一起认为“还有货”。',
        'difficulty': '进阶',
        'story': '限量纪念衫只剩 1 件，课堂脚本会并发提交多次下单。',
        'endpoint': '/labs/race/inventory-burst',
        'primary_class': '库存竞争',
        'secondary_class': '库存检查与扣减分离',
        'timing_class': '并发触发',
        'defense_focus': '条件更新 / 库存锁',
        'teacher_path': '非常适合讲“超卖”这种学生容易理解的真实业务后果。',
        'hints': [
            '看库存扣减是不是在同一原子操作里完成。',
            '只要多个请求都先看到 stock=1，后续都可能宣称成功。',
            '安全模式常见做法是 UPDATE ... WHERE stock > 0。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh race-inventory 重置库存。',
    },
    {
        'domain': 'race',
        'slug': 'wallet-burst',
        'title': 'L03 钱包并发扣款',
        'subtitle': '余额检查和扣款分开，会让多个并发请求都误以为自己有足够余额。',
        'difficulty': '高级',
        'story': '课堂钱包有 40 元，演示台会同时发起多次 20 元扣款。',
        'endpoint': '/labs/race/wallet-burst',
        'primary_class': '余额竞争',
        'secondary_class': '余额检查与扣款分离',
        'timing_class': '并发触发',
        'defense_focus': '原子余额扣减 / 锁',
        'teacher_path': '用“余额被扣成负数”这种直观结果讲竞争条件。',
        'hints': [
            '看服务端是否把 if balance >= amount 与 balance -= amount 分成了两步。',
            '并发下，这两步之间的窗口就是漏洞。',
            '安全模式要让条件检查和更新属于同一临界区。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh race-wallets 重置钱包。',
    },
    {
        'domain': 'race',
        'slug': 'seat-burst',
        'title': 'L04 单席位并发抢占',
        'subtitle': '最后一个名额如果靠普通状态字段控制，并发下可能被多个人同时拿到。',
        'difficulty': '高级',
        'story': '大师课最后 1 个席位对外开放，演示台会并发发起多次抢占。',
        'endpoint': '/labs/race/seat-burst',
        'primary_class': '名额竞争',
        'secondary_class': '最后一个资源抢占',
        'timing_class': '并发触发',
        'defense_focus': '事务 / 唯一约束 / 原子状态迁移',
        'teacher_path': '这关用来收束 race 条件：无论券、库存、余额还是席位，本质都是原子性丢失。',
        'hints': [
            '把这关和库存超卖对照看，会发现本质都是一个共享状态。',
            '关键不是资源名字不同，而是状态迁移没有原子化。',
            '安全模式通常会让状态检查与写入在同一个受控临界区。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh race-seats 重置席位。',
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
