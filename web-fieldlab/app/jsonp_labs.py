from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '回调函数名可控',
    '敏感数据跨域泄露',
    '伪修复 / 黑名单回调过滤',
    '带身份 JSONP / CSRF 旁路',
    'CORS 修了但 JSONP 没修',
]

LABS = [
    {
        'domain': 'jsonp',
        'slug': 'callback-reflect',
        'title': 'L01 JSONP 回调函数名可控',
        'subtitle': 'callback 参数如果不校验，本身就会变成可执行脚本的一部分。',
        'difficulty': '基础',
        'story': '旧版搜索接口为了兼容跨域，仍保留 JSONP 模式。',
        'endpoint': '/labs/jsonp/callback-reflect',
        'primary_class': '回调函数名可控',
        'secondary_class': 'callback 直接拼 JS',
        'timing_class': '脚本加载时触发',
        'defense_focus': '弃用 JSONP / 严格校验回调函数名',
        'teacher_path': '先讲 JSONP 为什么能跨域，再讲 callback 为什么本质是代码位置。',
        'hints': [
            '先确认响应头和响应体是不是 JavaScript，而不是 JSON。',
            'callback 如果直接拼到返回脚本里，本质就是可执行位置。',
            '安全模式应直接停用 JSONP 或只允许严格函数名模式。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'jsonp',
        'slug': 'profile-leak',
        'title': 'L02 认证资料通过 JSONP 泄露',
        'subtitle': '即便前端有 CORS 限制，JSONP 仍可能把敏感数据送给第三方页面。',
        'difficulty': '进阶',
        'story': '学员资料接口沿用 JSONP 兼容逻辑，会把用户资料包装成 callback(data)。',
        'endpoint': '/labs/jsonp/profile-leak',
        'primary_class': '敏感数据跨域泄露',
        'secondary_class': '带身份的 JSONP 响应',
        'timing_class': '脚本加载时触发',
        'defense_focus': '敏感接口禁用 JSONP / 改为受控 CORS',
        'teacher_path': '强调 JSONP 风险不只在 XSS，也在跨域读取敏感数据。',
        'hints': [
            '看接口返回的是不是当前用户的私有资料。',
            '如果第三方页面能用 script 标签直接拿到这些数据，就不是普通前端“展示问题”。',
            '安全模式要让敏感接口只返回 JSON，不再支持 callback 包装。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'jsonp',
        'slug': 'callback-blacklist',
        'title': 'L03 伪修复：黑名单回调过滤',
        'subtitle': '只替换几个危险字符，不代表 callback 就真正安全。',
        'difficulty': '进阶',
        'story': '开发者给 callback 做了 replace 过滤，但仍把剩余内容当 JS 函数名使用。',
        'endpoint': '/labs/jsonp/callback-blacklist',
        'primary_class': '伪修复 / 黑名单回调过滤',
        'secondary_class': '字符串 replace 过滤',
        'timing_class': '脚本加载时触发',
        'defense_focus': '正则白名单 / 彻底弃用 JSONP',
        'teacher_path': '拿它收尾：JSONP 的问题不适合靠补丁式黑名单修。',
        'hints': [
            '先看过滤器到底删除了什么，又保留了什么。',
            '只要 callback 最终仍然进入 JS 代码位，黑名单就很脆弱。',
            '真正安全的办法通常不是“再多删一点字符”。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'jsonp',
        'slug': 'csrf-via-jsonp',
        'title': 'L04 带身份 JSONP / CSRF 旁路',
        'subtitle': '即使加了 CSRF Token 防护，JSONP 仍可被第三方 <script> 跨域读取登录态数据。',
        'difficulty': '高级',
        'story': '账户中心保留了 JSONP 兼容接口，response 会带上当前登录用户的余额和邮箱。',
        'endpoint': '/labs/jsonp/csrf-via-jsonp',
        'primary_class': '带身份 JSONP / CSRF 旁路',
        'secondary_class': '带 Cookie 的 JSONP 响应',
        'timing_class': '脚本加载时触发',
        'defense_focus': '敏感接口禁止 JSONP / Cookie SameSite=Strict / Origin 白名单',
        'teacher_path': '把 CSRF 域和 JSONP 域串起来：CSRF Token 只能防写，不防读；JSONP 是读侧旁路。',
        'hints': [
            'PoC：在第三方页面写 <script src="/api/jsonp/account?callback=leak">，Cookie 自动带过去。',
            'safe 模式：服务端检测到带身份请求 + JSONP 直接拒绝。',
            '生产建议：所有带 Cookie 的接口都返回 application/json，并禁用 callback 参数。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'jsonp',
        'slug': 'cors-vs-jsonp',
        'title': 'L05 CORS 修了但 JSONP 没修',
        'subtitle': '/api/v2 已经收紧 CORS，但旧版 /api/jsonp/v1 仍 callback 可控 → 旁路。',
        'difficulty': '高级',
        'story': '前端团队迁到了带 Origin 白名单的 v2 API，旧 JSONP 接口被遗忘但仍上线。',
        'endpoint': '/labs/jsonp/cors-vs-jsonp',
        'primary_class': 'CORS 修了但 JSONP 没修',
        'secondary_class': '迁移遗留 / 双端点风险',
        'timing_class': '脚本加载时触发',
        'defense_focus': '迁移时下线旧端点 / 全量审计 callback 入口',
        'teacher_path': '强调"安全修复要看版本树全量"——只修新接口的 CORS 没有意义。',
        'hints': [
            'v2 API：fetch 带 Origin 校验，跨域直接拒绝。',
            'v1 JSONP：callback 仍可控，第三方 <script> 可绕过 CORS 拿到同样数据。',
            'safe 模式直接 410 下线 v1 端点。',
        ],
        'reset': '无需重置；该关卡默认只读。',
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
