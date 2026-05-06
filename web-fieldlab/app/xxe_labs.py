from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '本地文件实体',
    '外部实体到内网请求',
    '存储后二次解析',
    '参数实体 / 盲打',
    '错误回显抽取',
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
    {
        'domain': 'xxe',
        'slug': 'parameter-entity-blind',
        'title': 'L04 参数实体盲打（外接 DTD）',
        'subtitle': '用 % 参数实体引用外部 DTD，让解析器去内网拉文件并触发回调。',
        'difficulty': '高级',
        'story': '资产同步器允许外部 DTD（load_dtd=True），% 实体可叠加文件读取与 OOB 触发。',
        'endpoint': '/labs/xxe/parameter-entity-blind',
        'primary_class': '参数实体 / 盲打',
        'secondary_class': 'load_dtd / parameter entity',
        'timing_class': '解析时立即触发',
        'defense_focus': 'load_dtd=False + resolve_entities=False',
        'teacher_path': '展示"无回显也能读文件"——参数实体把读到的内容拼进新的实体。',
        'hints': [
            'PoC：通过 <!ENTITY % remote SYSTEM "http://intranet:7001/public/card"> 让解析器主动出网。',
            'safe 模式 load_dtd=False，外部 DTD 直接拒绝。',
            '观察：vuln 模式即使 XML body 没回显，解析器日志里也能看到外接 DTD 的请求。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'xxe',
        'slug': 'error-based-disclosure',
        'title': 'L05 错误信息回显抽取',
        'subtitle': '即使没有正常输出通道，畸形实体引用也能把文件内容塞进 parser error。',
        'difficulty': '高级',
        'story': '上传通道把解析失败的 XML 错误堆栈完整回显给前端，攻击者借此读 /etc/hostname。',
        'endpoint': '/labs/xxe/error-based-disclosure',
        'primary_class': '错误回显抽取',
        'secondary_class': 'parser error leak',
        'timing_class': '解析失败时触发',
        'defense_focus': '禁止把解析错误明文回显 + 安全解析器',
        'teacher_path': '强调"错误信息也是输出通道"——日志和 5xx 页面同样要做净化。',
        'hints': [
            'PoC：让 file 实体出现在一个会触发解析错误的位置（如非法 NCName），错误里就会带文件内容。',
            'safe 模式不解析实体，且只回显通用错误。',
            '生产建议：5xx 页面只显示 trace_id，详细信息只进日志。',
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
