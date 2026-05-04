from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '未授权访问',
    '水平越权：读取',
    '水平越权：修改',
    '垂直越权：页面访问',
    '垂直越权：敏感操作',
]

LABS = [
    {
        'domain': 'authz',
        'slug': 'unauth-report',
        'title': 'L00 未授权访问：公开敏感报表',
        'subtitle': '不是所有授权问题都发生在“已登录用户”之间，有些页面甚至完全没做登录校验。',
        'difficulty': '基础',
        'story': '教务纪律报表页原本以为“知道链接的人很少”，结果后端完全没有登录检查。',
        'endpoint': '/labs/authz/unauth-report',
        'primary_class': '未授权访问',
        'secondary_class': '无登录校验 / 直接暴露敏感页面',
        'timing_class': '立即触发',
        'defense_focus': '先做认证，再做授权',
        'teacher_path': '把“未授权”与“越权”区分开：前者连登录门槛都没有，后者是登录后权限边界错误。',
        'hints': [
            '先确认访问敏感页面前是否要求登录。',
            '如果连登录状态都不检查，就不是对象级越权，而是未授权暴露。',
            '安全模式至少要先验证会话，再谈角色或对象归属。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'authz',
        'slug': 'horizontal-orders',
        'title': 'L01 水平越权：订单详情读取',
        'subtitle': '同角色用户之间不应互相读取彼此的敏感对象。',
        'difficulty': '基础',
        'story': '学员纪念品订单页只要求登录，却没有校验对象归属。',
        'endpoint': '/labs/authz/horizontal-orders',
        'primary_class': '水平越权：读取',
        'secondary_class': 'IDOR / 对象归属缺失',
        'timing_class': '立即触发',
        'defense_focus': '对象级授权校验',
        'teacher_path': '这是讲 IDOR 最直观的一关：同一角色，换个 id 就能看别人的东西。',
        'hints': [
            '先确认系统是否只做“已登录”检查，而没做“对象属于谁”的检查。',
            '如果参数只决定取哪条记录，却不绑定当前用户，就容易发生水平越权。',
            '安全模式必须把对象 owner 和当前用户一起校验。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh authz-orders 恢复订单数据。',
    },
    {
        'domain': 'authz',
        'slug': 'horizontal-notes',
        'title': 'L02 水平越权：他人便签修改',
        'subtitle': '能读别人的数据是一类问题，能改别人的数据则更严重。',
        'difficulty': '进阶',
        'story': '课后总结便签只按 note_id 更新，没有绑定 owner。',
        'endpoint': '/labs/authz/horizontal-notes',
        'primary_class': '水平越权：修改',
        'secondary_class': '对象更新缺少 owner 校验',
        'timing_class': '立即触发',
        'defense_focus': '写操作同样做对象级授权',
        'teacher_path': '用它讲“授权不仅影响读，也影响写”。',
        'hints': [
            '看更新接口是根据 note_id 直接修改，还是同时校验当前用户。',
            '只要能定位到别人的对象，又没有 owner 检查，就可能发生横向篡改。',
            '安全模式要让 UPDATE / DELETE 也绑定 owner 条件。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh authz-notes 恢复便签。',
    },
    {
        'domain': 'authz',
        'slug': 'vertical-admin-report',
        'title': 'L03 垂直越权：管理报表访问',
        'subtitle': '前端隐藏入口不等于真正鉴权。',
        'difficulty': '基础',
        'story': '管理报表页在菜单里只给管理员显示，但路由本身没有做角色校验。',
        'endpoint': '/labs/authz/vertical-admin-report',
        'primary_class': '垂直越权：页面访问',
        'secondary_class': '仅前端隐藏 / 后端未校验',
        'timing_class': '立即触发',
        'defense_focus': '后端强制角色校验',
        'teacher_path': '专门用来打掉“把按钮藏起来就算权限控制”的误区。',
        'hints': [
            '不要只看菜单是否隐藏，要看实际路由是否做后端鉴权。',
            '如果用户能直接访问敏感页面地址，前端隐藏入口没有意义。',
            '安全模式必须在服务器端检查角色。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'authz',
        'slug': 'vertical-ticket-close',
        'title': 'L04 垂直越权：敏感工单操作',
        'subtitle': '高权限动作不应只靠“按钮是否展示”控制。',
        'difficulty': '进阶',
        'story': '关闭工单的 POST 接口默认相信前端只有管理员会点到它。',
        'endpoint': '/labs/authz/vertical-ticket-close',
        'primary_class': '垂直越权：敏感操作',
        'secondary_class': '动作级授权缺失',
        'timing_class': '立即触发',
        'defense_focus': '动作级后端鉴权 / 审计',
        'teacher_path': '这关适合讲页面访问与敏感动作是两层不同的授权点。',
        'hints': [
            '看 POST 操作接口是否在服务器端再次校验角色。',
            '只要操作接口本身不做限制，隐藏按钮并不能阻止直接提交请求。',
            '安全模式应让动作级别的每个接口都执行角色检查。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh authz-tickets 恢复工单状态。',
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
