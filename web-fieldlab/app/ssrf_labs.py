from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '任意目标抓取',
    '字符串白名单绕过',
    '重定向链 SSRF',
    '盲 SSRF / 副作用观测',
]

LABS = [
    {
        'domain': 'ssrf',
        'slug': 'basic-fetch',
        'title': 'L01 任意目标抓取',
        'subtitle': '服务端替用户发请求，本质上就是把网络信任边界交出去了。',
        'difficulty': '基础',
        'story': '链接预览组件会在服务端抓取目标页面摘要。',
        'endpoint': '/labs/ssrf/basic-fetch',
        'primary_class': '任意目标抓取',
        'secondary_class': '服务端回显型 SSRF',
        'timing_class': '立即触发',
        'defense_focus': '协议 / 主机 / 网段限制',
        'teacher_path': '先讲“不是浏览器请求，而是服务端请求”，再引导学生打内部地址。',
        'hints': [
            '确认请求到底从谁发出：浏览器还是服务端。',
            '如果服务端能访问浏览器访问不到的主机，价值就会立刻提升。',
            '安全模式至少要限制协议和私有网段。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'ssrf',
        'slug': 'allowlist-bypass',
        'title': 'L02 字符串白名单绕过',
        'subtitle': '只看 URL 前缀的“白名单”很容易被解析差异绕过。',
        'difficulty': '进阶',
        'story': '预览服务只允许抓取 `preview-gateway`，但校验只用了 startswith。',
        'endpoint': '/labs/ssrf/allowlist-bypass',
        'primary_class': '字符串白名单绕过',
        'secondary_class': 'userinfo / 解析差异',
        'timing_class': '立即触发',
        'defense_focus': '解析后再校验 hostname',
        'teacher_path': '适合讲 URL 的“看起来像什么”和“真正会连到哪里”是两回事。',
        'hints': [
            '先区分字符串检查和真正的 URL 解析结果。',
            '如果过滤器只做 startswith，可能根本没看实际 hostname。',
            '安全模式必须在 parse 之后看 scheme/hostname/port。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'ssrf',
        'slug': 'redirect-follow',
        'title': 'L03 重定向链 SSRF',
        'subtitle': '即使第一跳看起来安全，自动跟随重定向也可能把请求带进内网。',
        'difficulty': '进阶',
        'story': '预览器要求首个域名必须是 `preview-gateway`，但默认会跟随 302。',
        'endpoint': '/labs/ssrf/redirect-follow',
        'primary_class': '重定向链 SSRF',
        'secondary_class': '首跳安全 / 终跳危险',
        'timing_class': '立即触发',
        'defense_focus': '禁用自动重定向或逐跳重验',
        'teacher_path': '强调“不是校验一次就结束”，后续跳转同样要视作新请求。',
        'hints': [
            '先看抓取器是否自动跟随 3xx。',
            '如果只校验第一跳地址，重定向链就可能变成新的入口。',
            '安全模式可以禁用重定向，或对每一跳都做相同校验。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'ssrf',
        'slug': 'blind-log',
        'title': 'L04 盲 SSRF 与副作用日志',
        'subtitle': '页面不回显响应体，也可能通过耗时、状态码和服务器日志观察副作用。',
        'difficulty': '高级',
        'story': '后台探测器只告诉用户“抓取任务已完成”，实际结果写入服务端日志。',
        'endpoint': '/labs/ssrf/blind-log',
        'primary_class': '盲 SSRF / 副作用观测',
        'secondary_class': '状态码 / 耗时 / 服务器日志',
        'timing_class': '立即触发',
        'defense_focus': '限制出站能力 / 缩小访问面 / 审计日志',
        'teacher_path': '把 SSRF 从“读响应体”扩展到“观察副作用”，更接近真实业务。',
        'hints': [
            '如果页面不直接回显，也要看有没有时间差、状态差或日志差。',
            '内部服务的可达性未必通过正文体现，也可能通过副作用被证明。',
            '安全模式重点是减少服务端能触达的范围。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh ssrf 清空 SSRF 日志。',
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
