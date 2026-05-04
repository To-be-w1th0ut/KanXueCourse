from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '直接模板渲染',
    '表达式包装',
    '存储后二次渲染',
    '受信片段拼接',
]

LABS = [
    {
        'domain': 'ssti',
        'slug': 'reflected-template',
        'title': 'L01 直接 render_template_string',
        'subtitle': '把用户输入直接当成模板源码渲染，是最直观的 SSTI 起点。',
        'difficulty': '基础',
        'story': '欢迎卡片预览器允许老师自定义模板片段。',
        'endpoint': '/labs/ssti/reflected-template',
        'primary_class': '直接模板渲染',
        'secondary_class': 'Jinja 表达式执行',
        'timing_class': '立即触发',
        'defense_focus': '不要把不可信字符串送进模板引擎',
        'teacher_path': '先让学生理解“模板语法就是代码”，再讲为什么普通 HTML 转义根本不够。',
        'hints': [
            '观察输入是不是被当作模板源码，而不是普通变量值。',
            '如果输入里的模板语法被解析，说明执行边界已经在服务端丢失。',
            '安全模式应该把模板当数据展示，而不是继续交给引擎。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'ssti',
        'slug': 'expression-wrapper',
        'title': 'L02 表达式包装型 SSTI',
        'subtitle': '用户只提交表达式，服务端却主动替它补上模板定界符。',
        'difficulty': '进阶',
        'story': '报表配置器只让老师输入“表达式主体”，后端自动补成完整模板。',
        'endpoint': '/labs/ssti/expression-wrapper',
        'primary_class': '表达式包装',
        'secondary_class': '服务端主动拼模板',
        'timing_class': '立即触发',
        'defense_focus': '不要拼接模板语法；对可计算表达式做白名单',
        'teacher_path': '这关适合讲“用户没写 {{ }} 不代表后端没帮他补上”。',
        'hints': [
            '看输入是不是被包进了某个固定模板结构。',
            '一旦后端把表达式包进 {{ ... }}，用户控制的就不再只是普通文本。',
            '安全模式通常需要改成显式字段映射，而不是继续让表达式可执行。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'ssti',
        'slug': 'stored-mail',
        'title': 'L03 存储后二次渲染邮件模板',
        'subtitle': '第一次只是保存模板，真正的执行发生在后续预览环节。',
        'difficulty': '高级',
        'story': '教务邮件模板保存在数据库里，预览页每次都会重新渲染。',
        'endpoint': '/labs/ssti/stored-mail',
        'primary_class': '存储后二次渲染',
        'secondary_class': '模板持久化传播',
        'timing_class': '存储后触发',
        'defense_focus': '存储后再次输出时仍不能信任模板内容',
        'teacher_path': '把 SSTI 也讲成“第一次存储、第二次触发”的生命周期问题。',
        'hints': [
            '先确认模板会不会被保存，再确认预览时是否重新喂给引擎。',
            '如果数据库里的内容被当作模板源码，第一次保存再安全也没意义。',
            '修复时不要只在保存入口做过滤。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh ssti-mail 恢复默认邮件模板。',
    },
    {
        'domain': 'ssti',
        'slug': 'theme-fragment',
        'title': 'L04 受信片段拼接',
        'subtitle': '开发以为“只是主题片段”，却把不可信片段拼进完整模板。',
        'difficulty': '高级',
        'story': '主题编辑器允许自定义横幅片段，并和系统模板合并渲染。',
        'endpoint': '/labs/ssti/theme-fragment',
        'primary_class': '受信片段拼接',
        'secondary_class': '大模板内嵌小模板',
        'timing_class': '立即触发',
        'defense_focus': '主题片段做白名单或完全取消模板能力',
        'teacher_path': '这关适合讲“受信模板 + 不可信局部片段”也是危险组合。',
        'hints': [
            '观察系统是不是先拿用户片段拼出一个更大的模板，再一起渲染。',
            '局部可控不代表风险小，只要最后进入引擎就是同等危险。',
            '安全模式通常会改成预定义组件或纯文本占位。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh ssti-theme 恢复默认主题片段。',
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
