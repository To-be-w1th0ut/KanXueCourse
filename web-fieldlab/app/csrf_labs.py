from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '无 Token 状态修改',
    '伪防护：Referer / Header 检查',
    'JSON API / Content-Type CSRF',
    '退出登录 / 偏好修改',
]

LABS = [
    {
        'domain': 'csrf',
        'slug': 'transfer-no-token',
        'title': 'L01 无 Token 转账',
        'subtitle': '最经典的 CSRF：已登录用户的状态修改请求没有任何一次性防护。',
        'difficulty': '基础',
        'story': '课堂钱包支持表单转账，但表单没有 CSRF token。',
        'endpoint': '/labs/csrf/transfer-no-token',
        'primary_class': '无 Token 状态修改',
        'secondary_class': '表单 POST 无一次性令牌',
        'timing_class': '受害者访问恶意页面时触发',
        'defense_focus': 'CSRF Token / SameSite / 二次确认',
        'teacher_path': '第一关先讲清 CSRF 的核心：浏览器会自动带上受害者自己的身份。',
        'hints': [
            '先确认状态修改请求是否需要任何随机 token。',
            '如果浏览器会自动携带 session，而请求本身又没有额外校验，就满足了 CSRF 条件。',
            '安全模式至少需要一次性 token。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh csrf 重置钱包与日志。',
    },
    {
        'domain': 'csrf',
        'slug': 'referer-check',
        'title': 'L02 伪防护：只查 Referer',
        'subtitle': 'Referer 检查可以辅助，但把它当唯一防线通常不够。',
        'difficulty': '进阶',
        'story': '安全同学要求加来源校验，开发只写了一个脆弱的字符串包含判断。',
        'endpoint': '/labs/csrf/referer-check',
        'primary_class': '伪防护：Referer / Header 检查',
        'secondary_class': '字符串 contains 校验',
        'timing_class': '跨站自动提交时触发',
        'defense_focus': '严格 Origin/Referer + Token，不依赖字符串包含',
        'teacher_path': '这关适合讲“辅助信号”和“核心防护”不是一回事。',
        'hints': [
            '先看服务端如何判断请求来源。',
            '如果只是 contains 某个域名，很可能既不严格也不稳定。',
            '安全模式应把来源校验当辅助，再叠加 token。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh csrf 重置钱包与日志。',
    },
    {
        'domain': 'csrf',
        'slug': 'json-settings',
        'title': 'L03 JSON API 偏好修改',
        'subtitle': '改成 JSON body 不会自动消除 CSRF 风险。',
        'difficulty': '进阶',
        'story': '账户偏好接口升级成 JSON API，但仍使用 Cookie 会话。',
        'endpoint': '/labs/csrf/json-settings',
        'primary_class': 'JSON API / Content-Type CSRF',
        'secondary_class': 'Cookie 会话 + 缺少 CSRF token',
        'timing_class': '跨站脚本或表单封装时触发',
        'defense_focus': 'Token / SameSite / 严格 Content-Type 与认证方案分离',
        'teacher_path': '重点打破“JSON 就天然防 CSRF”的误区。',
        'hints': [
            '看接口认证是不是仍然依赖浏览器自动附带的 Cookie。',
            '如果答案是是，那就还存在被第三方页面借用身份的空间。',
            '安全模式应把 token 验证和 Cookie 会话一起考虑。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh csrf-wallets 重置账户偏好。',
    },
    {
        'domain': 'csrf',
        'slug': 'logout-and-mfa',
        'title': 'L04 登出 / MFA 偏好 CSRF',
        'subtitle': 'CSRF 不只会转账，也会破坏安全配置和会话状态。',
        'difficulty': '基础',
        'story': '账户中心允许一键关闭 MFA 或登出全部设备，但没有 token 校验。',
        'endpoint': '/labs/csrf/logout-and-mfa',
        'primary_class': '退出登录 / 偏好修改',
        'secondary_class': '安全配置变更无 CSRF 防护',
        'timing_class': '受害者打开恶意页面时触发',
        'defense_focus': '敏感操作重新认证 / Token / 双击确认',
        'teacher_path': '这关提醒学生：CSRF 影响的是“以受害者身份发出的状态修改”，不止财务动作。',
        'hints': [
            '看关闭 MFA、退出登录这样的动作是否也只是普通 POST。',
            '只要浏览器能自动带身份，安全配置同样可能被跨站页面改掉。',
            '安全模式对敏感安全动作应更严格。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh csrf-wallets 重置账户偏好。',
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
