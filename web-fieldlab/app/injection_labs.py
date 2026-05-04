from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '代码注入',
    '命令注入',
]

LABS = [
    {
        'domain': 'injection',
        'slug': 'python-eval',
        'title': 'L01 Python eval 代码注入',
        'subtitle': '把用户表达式直接交给 eval，本质上就是把解释器暴露给了输入。',
        'difficulty': '基础',
        'story': '价格试算台允许老师输入“公式”，服务端直接 eval。',
        'endpoint': '/labs/injection/python-eval',
        'primary_class': '代码注入',
        'secondary_class': 'eval / 表达式执行',
        'timing_class': '立即触发',
        'defense_focus': 'AST 白名单 / 禁止解释执行不可信表达式',
        'teacher_path': '用最直观的 eval 把“代码注入”概念立住，再讲安全替代。',
        'hints': [
            '先观察输入是不是被当成代码求值，而不是普通字符串。',
            '只要用户能影响解释器执行内容，风险就已经成立。',
            '安全模式通常用 AST 白名单或显式映射，不继续让表达式自由执行。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'injection',
        'slug': 'stored-exec',
        'title': 'L02 存储后 exec 规则执行',
        'subtitle': '用户提交的脚本先存下来，真正的执行发生在后续规则预演。',
        'difficulty': '高级',
        'story': '自动化规则编辑器允许老师写 Python 片段，预演时用 exec 跑起来。',
        'endpoint': '/labs/injection/stored-exec',
        'primary_class': '代码注入',
        'secondary_class': 'exec / 存储后二次执行',
        'timing_class': '存储后触发',
        'defense_focus': '禁用脚本能力 / DSL 白名单',
        'teacher_path': '这关把代码注入也讲成生命周期问题：保存和执行是两步。',
        'hints': [
            '先确认规则会不会被保存，再看预演是不是把它当脚本执行。',
            '数据库里的脚本内容并不会因为“已经保存”就变安全。',
            '安全模式应把规则改成固定 DSL 或受限字段。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh injection-snippets 重置规则。',
    },
    {
        'domain': 'injection',
        'slug': 'command-diagnose',
        'title': 'L03 诊断命令拼接',
        'subtitle': 'shell=True + 字符串拼接，是命令注入最常见的课堂入口。',
        'difficulty': '基础',
        'story': '运维诊断面板会把目标主机拼进 shell 命令里。',
        'endpoint': '/labs/injection/command-diagnose',
        'primary_class': '命令注入',
        'secondary_class': 'shell=True / 参数拼接',
        'timing_class': '立即触发',
        'defense_focus': '参数列表调用 / 禁用 shell',
        'teacher_path': '这关适合讲“命令解释器也是解释器”，和代码注入一脉相承。',
        'hints': [
            '看服务端是不是把整条命令拼成一个字符串后交给 shell。',
            '只要 shell 会重新解析用户内容，输入就可能变成新的命令片段。',
            '安全模式要用参数数组，避免 shell 参与二次解析。',
        ],
        'reset': '无需重置；该关卡默认只读。',
    },
    {
        'domain': 'injection',
        'slug': 'command-grep',
        'title': 'L04 grep 日志检索命令注入',
        'subtitle': '不是只有系统命令诊断台，日常运维工具同样可能把用户词条拼进 shell。',
        'difficulty': '进阶',
        'story': '日志检索器为了省事直接拼出 `grep -n <keyword> file`。',
        'endpoint': '/labs/injection/command-grep',
        'primary_class': '命令注入',
        'secondary_class': 'grep / 查询参数拼接',
        'timing_class': '立即触发',
        'defense_focus': '参数数组 / 固定子命令 / 转义不是根治',
        'teacher_path': '这关能让学生看到：即使只是“搜索关键词”，也可能进入命令解释链。',
        'hints': [
            '关注 keyword 最终是不是成为 shell 命令的一部分。',
            '如果命令字符串里直接拼 keyword，grep 只是外壳，真正危险的是 shell。',
            '安全模式要把 keyword 当普通参数传入，不拼整个命令串。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh injection 重置规则与日志。',
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
