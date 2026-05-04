from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '本地文件实体',
    '外部实体到内网请求',
    '存储后二次解析',
]

LABS = [
    {
        'domain': 'xxe',
        'slug': 'local-file',
        'title': 'L01 XXE 读取本地文件',
        'subtitle': 'XML 解析器一旦允许外部实体，文件系统就可能变成新的数据源。',
        'difficulty': '基础',
        'story': '订单导入器支持 XML，旧版解析器开启了实体解析。',
        'endpoint': '/labs/xxe/local-file',
        'primary_class': '本地文件实体',
        'secondary_class': 'SYSTEM file://',
        'timing_class': '立即触发',
        'defense_focus': '禁用实体解析 / 使用安全解析器',
        'teacher_path': '第一关先让学生理解：XXE 的核心是“解析器替你再去读别的东西”。',
        'hints': [
            '先确认解析器是否启用了实体展开。',
            '如果 XML 内容里能引用本地文件，说明输入边界已经延伸到文件系统。',
            '安全模式重点是解析器配置，而不是事后做字符串替换。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'xxe',
        'slug': 'internal-ssrf',
        'title': 'L02 XXE 打内网 HTTP 目标',
        'subtitle': '外部实体不只会读文件，也可能帮解析器发起网络请求。',
        'difficulty': '进阶',
        'story': 'XML 资产同步器与内网服务互通，解析器因此也能访问内部地址。',
        'endpoint': '/labs/xxe/internal-ssrf',
        'primary_class': '外部实体到内网请求',
        'secondary_class': 'SYSTEM http://',
        'timing_class': '立即触发',
        'defense_focus': '禁用外部实体 / 禁止网络解析',
        'teacher_path': '把 XXE 与 SSRF 串起来讲，让学生看到解析器也会代发网络请求。',
        'hints': [
            '看实体是否只支持 file://，还是也会去请求 http:// 资源。',
            '如果解析器所在服务器能访问内网，XXE 的影响面会立刻扩大。',
            '安全模式要同时关掉实体解析和网络访问。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'xxe',
        'slug': 'stored-xml',
        'title': 'L03 存储后二次 XML 解析',
        'subtitle': '第一次只是保存 XML 文档，真正危险在后续“预览 / 校验”动作。',
        'difficulty': '高级',
        'story': '报销单 XML 会被存库，审核页每次打开都重新解析。',
        'endpoint': '/labs/xxe/stored-xml',
        'primary_class': '存储后二次解析',
        'secondary_class': '持久化 XML 文档',
        'timing_class': '存储后触发',
        'defense_focus': '保存前后都不信任 XML / 使用安全解析器',
        'teacher_path': '用生命周期把 XXE 讲成“存储型解析器漏洞”。',
        'hints': [
            '先找“保存 XML”的入口，再找“解析 XML”的后续流程。',
            '只要后续还会重新解析，第一次是否马上报错并不重要。',
            '安全模式应让后续解析链也使用安全配置。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh xxe-docs 重置 XML 文档。',
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
