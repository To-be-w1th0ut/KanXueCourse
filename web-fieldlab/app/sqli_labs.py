from __future__ import annotations

from collections import defaultdict

POSITION_ORDER = [
    "值上下文注入",
    "结构上下文注入",
    "语句级注入",
    "动态 SQL 注入",
]

OBSERVATION_ORDER = [
    "直接回显型",
    "报错型",
    "布尔盲注",
    "时间盲注",
    "带外潜力型",
]

IMPACT_ORDER = [
    "认证绕过",
    "数据读取",
    "数据枚举",
    "数据篡改",
    "数据删除",
    "语句扩展",
    "错误修复对照",
]

TIMING_ORDER = [
    "一次注入",
    "二次注入",
]

DATABASE_ORDER = [
    "MySQL / MariaDB",
    "PostgreSQL",
    "SQL Server",
    "Oracle",
    "SQLite",
]

LABS = [
    {
        "slug": "login-bypass",
        "title": "L01 登录网关绕过",
        "subtitle": "实战感最强的起点：从单条认证语句切入业务后台。",
        "difficulty": "基础",
        "story": "蓝队值班台的旧版认证门户仍在使用字符串拼接查询。",
        "endpoint": "/labs/sqli/login-bypass",
        "tables": ["users"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE 字符串值 / 认证条件",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "认证绕过",
        "impact_detail": "改写认证逻辑，越过用户名密码校验。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "先讲值上下文，再讲认证逻辑如何被恒真条件改写。",
        "hints": [
            "先观察登录失败和成功的响应差异，确认是否存在布尔条件控制。",
            "注意用户名和密码是如何进入 WHERE 条件的，尝试让条件恒真。",
            "如果课堂上需要稳定演示，可先以 admin 账户为目标，再观察返回的角色字段。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "product-union",
        "title": "L02 商品检索 UNION 泄露",
        "subtitle": "模拟电商后台检索接口，被动输入框变成信息拼接器。",
        "difficulty": "基础",
        "story": "运营同学用商品模糊搜索查库存，但接口没有参数化。",
        "endpoint": "/labs/sqli/product-union",
        "tables": ["products", "lab_flags"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE / LIKE 模糊查询值",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据读取",
        "impact_detail": "通过 UNION 扩展结果集，跨表读出额外数据。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "值上下文进入 WHERE，再引出 UNION 作为回显型取数方式。",
        "hints": [
            "先确认返回列数，再思考哪些列适合承接文本数据。",
            "留意页面最终渲染的是哪几列，数值列和文本列类型要兼容。",
            "敏感目标并不一定在 products 表里，课堂里可以尝试拼接其他表。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "error-ticket",
        "title": "L03 工单详情报错注入",
        "subtitle": "错误信息被原样回显，数据库异常直接变成信息通道。",
        "difficulty": "进阶",
        "story": "运维工单详情页为方便排障，直接把数据库报错展示给一线人员。",
        "endpoint": "/labs/sqli/error-ticket",
        "tables": ["support_tickets", "lab_flags"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE 数值值 / 详情 id",
        "timing_class": "一次注入",
        "observation_class": "报错型",
        "impact_class": "数据枚举",
        "impact_detail": "通过数据库异常把结构信息或目标数据拼进错误消息。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle"],
        "teacher_path": "讲数值上下文不依赖引号，再引出详细错误回显的危险。",
        "hints": [
            "观察 id 参数是否处于数字上下文。",
            "当语句本身执行出错时，页面是否把数据库异常完整展示了出来？",
            "如果能让数据库在错误字符串里拼接查询结果，就能实现报错外带。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "employee-blind",
        "title": "L04 门禁查询布尔盲注",
        "subtitle": "页面只告诉你“存在 / 不存在”，但这已经足够。",
        "difficulty": "进阶",
        "story": "访客登记系统隐藏了员工详情，只保留门禁编号存在性判断。",
        "endpoint": "/labs/sqli/employee-blind",
        "tables": ["employees", "lab_flags"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE 字符串值 / 存在性判断",
        "timing_class": "一次注入",
        "observation_class": "布尔盲注",
        "impact_class": "数据枚举",
        "impact_detail": "借真假响应逐位枚举数据库信息。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "讲“没有数据回显，不等于没有数据通道”。",
        "hints": [
            "页面不回显字段值，但会回显真假。真假本身就是侧信道。",
            "尝试构造一个原本不存在的 badge，再用 AND / OR 改写条件。",
            "逐位猜解时，先从数据库名、用户、固定 flag 前缀这类稳定目标入手。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "shipping-time",
        "title": "L05 物流接口时间盲注",
        "subtitle": "响应包没有泄露数据，但时间差会说话。",
        "difficulty": "进阶",
        "story": "物流客服接口只回“状态是否可见”，却把延时原样暴露给前端。",
        "endpoint": "/labs/sqli/shipping-time",
        "tables": ["orders", "lab_flags"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE 字符串值 / 订单号",
        "timing_class": "一次注入",
        "observation_class": "时间盲注",
        "impact_class": "数据枚举",
        "impact_detail": "利用时间侧信道探测真假条件。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle"],
        "teacher_path": "讲侧信道，把“看不到结果”升级为“照样能探测条件真假”。",
        "hints": [
            "先基线测试正常请求耗时，再对比异常延时。",
            "如果数据库支持 sleep 一类函数，真假条件可以映射成时间差。",
            "课堂上建议先猜数据库名首字符，便于学生快速看到时间变化。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "report-stacked",
        "title": "L06 审计报表堆叠查询",
        "subtitle": "一次请求，多条语句，影响面从读扩大到改。",
        "difficulty": "高级",
        "story": "旧版报表导出为了兼容历史脚本，数据库连接开启了 multi-statements。",
        "endpoint": "/labs/sqli/report-stacked",
        "tables": ["audit_logs", "grades"],
        "position_class": "语句级注入",
        "position_detail": "SELECT 查询被扩展为多语句执行",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "语句扩展",
        "impact_detail": "从单条查询升级为额外 UPDATE / DELETE / INSERT。",
        "database_profiles": ["MySQL / MariaDB", "SQL Server"],
        "teacher_path": "先讲查询语句，再讲驱动开启 multi-statements 后的放大效应。",
        "hints": [
            "观察驱动是否允许一条输入触发多条 SQL。",
            "如果第一条语句只是查询，第二条语句就可能是更新、删除或插入。",
            "验证影响时，优先改可恢复的数据表，例如 grades。",
        ],
        "reset": "使用 /scripts/reset_lab.sh report-stacked 恢复相关数据。",
    },
    {
        "slug": "second-order",
        "title": "L07 二次注入：保存筛选器",
        "subtitle": "第一次输入看似安全，真正的注入发生在稍后的后台报表。",
        "difficulty": "高级",
        "story": "分析师可以保存常用部门筛选条件，报表页会复用它生成 SQL。",
        "endpoint": "/labs/sqli/second-order",
        "tables": ["saved_filters", "employees", "lab_flags"],
        "position_class": "动态 SQL 注入",
        "position_detail": "数据库中存储值被二次拼回 WHERE 条件",
        "timing_class": "二次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据读取",
        "impact_detail": "保存的 payload 在后续动态报表中被重新解释。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "讲生命周期：第一次输入存储，第二次读取拼接才真正触发。",
        "hints": [
            "先找“存储用户输入”的位置，再找“重新使用该输入”的位置。",
            "注意第一次写入可能是安全的，第二次读取拼接才是漏洞触发点。",
            "课堂上可把 payload 保存后再去报表页触发，帮助学生理解生命周期。",
        ],
        "reset": "使用 /scripts/reset_lab.sh second-order 清空已保存的筛选器。",
    },
    {
        "slug": "leaderboard-sort",
        "title": "L08 排行榜排序 / LIMIT 注入",
        "subtitle": "不仅值要校验，列名、方向、分页参数也必须白名单。",
        "difficulty": "进阶",
        "story": "教务排行页允许前端自定义排序字段和展示数量。",
        "endpoint": "/labs/sqli/leaderboard-sort",
        "tables": ["grades"],
        "position_class": "结构上下文注入",
        "position_detail": "ORDER BY / ASC-DESC / LIMIT 结构位",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据枚举",
        "impact_detail": "通过排序表达式和分页位影响查询结构。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "这关专门讲“不是值位，参数化不够，必须白名单”。",
        "hints": [
            "ORDER BY 后面通常不是字符串字面量，而是列名或表达式。",
            "如果开发者直接拼接 sort / dir / limit，这里仍然可能注入。",
            "修复时不能用占位符绑定列名，必须做严格白名单。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "grade-editor",
        "title": "L09 成绩调整 UPDATE 注入",
        "subtitle": "SQL 注入不只会“读”，也会直接改业务数据。",
        "difficulty": "进阶",
        "story": "班主任补分工具允许输入加分表达式和评语。",
        "endpoint": "/labs/sqli/grade-editor",
        "tables": ["grades"],
        "position_class": "语句级注入",
        "position_detail": "UPDATE 的 SET / WHERE 子句",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据篡改",
        "impact_detail": "将单条更新放大为批量或任意修改。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "从读漏洞过渡到写漏洞，强调业务完整性破坏。",
        "hints": [
            "关注 SET 子句和 WHERE 子句是否都由用户输入拼接。",
            "一旦 WHERE 可以被改写，影响范围就可能从单条记录扩展到整表。",
            "修复时别只绑定 student_no，也要限制 bonus 的类型和 remark 的长度。",
        ],
        "reset": "使用 /scripts/reset_lab.sh grade-editor 恢复成绩数据。",
    },
    {
        "slug": "api-json-sqli",
        "title": "L10 JSON API 参数注入",
        "subtitle": "前端换成 JSON body，不等于注入风险自动消失。",
        "difficulty": "进阶",
        "story": "客服查询订单的接口升级成 JSON，但后端仍旧拼接 SQL。",
        "endpoint": "/labs/sqli/api-json-sqli",
        "tables": ["orders", "lab_flags"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE / LIKE + 数值比较，输入来自 JSON body",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据读取",
        "impact_detail": "JSON 只是载体，值进入 SQL 后依旧能改写查询。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "把页面表单场景扩展到 API，统一“输入就是输入”的认知。",
        "hints": [
            "观察 JSON 字段最终进入了哪些比较条件。",
            "数值字段如果直接拼接，同样可以成为注入点。",
            "前端有个内置请求面板，课堂上可以用它展示 API 层注入。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "faux-fix",
        "title": "L11 伪修复：黑名单过滤",
        "subtitle": "把关键字 replace 掉，不代表真正安全。",
        "difficulty": "基础",
        "story": "某开发以为把 union / select / or 替换为空串就安全了。",
        "endpoint": "/labs/sqli/faux-fix",
        "tables": ["users"],
        "position_class": "值上下文注入",
        "position_detail": "WHERE 字符串值 + 黑名单伪修复",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "错误修复对照",
        "impact_detail": "演示“过滤关键字”并没有修复语法边界。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "用于课程收束：为什么伪修复不可靠，为什么要回到边界控制。",
        "hints": [
            "先想想这个过滤器覆盖了哪些关键字、哪些没覆盖。",
            "SQL 里实现“恒真”的写法不止一种。",
            "课程重点不是找最花哨 payload，而是让学生理解黑名单为什么不可靠。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
    {
        "slug": "orm-misuse",
        "title": "L12 ORM 误用",
        "subtitle": "用了 ORM / text() 也照样可能被 f-string 打回原形。",
        "difficulty": "进阶",
        "story": "团队逐步迁移到 SQLAlchemy，但有些查询仍然手写 SQL。",
        "endpoint": "/labs/sqli/orm-misuse",
        "tables": ["products", "lab_flags"],
        "position_class": "动态 SQL 注入",
        "position_detail": "ORM text()/raw SQL 中的动态字符串拼接",
        "timing_class": "一次注入",
        "observation_class": "直接回显型",
        "impact_class": "数据读取",
        "impact_detail": "框架调用点并没有阻止用户输入改变原始 SQL。",
        "database_profiles": ["MySQL / MariaDB", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "teacher_path": "讲“用了 ORM”≠“没有 SQLi”，关键仍是是否绑定参数。",
        "hints": [
            "观察 ORM 是否真的在“绑定参数”，还是只是帮你执行了一段字符串。",
            "text() 不是问题，问题是 text() 里塞进去的内容怎么来的。",
            "课堂上可把它和前面的 UNION 检索关卡对照讲。",
        ],
        "reset": "无需重置；该关卡默认只读。",
    },
]


for lab in LABS:
    lab.setdefault("domain", "sqli")
    lab.setdefault("primary_class", lab.get("position_class", "值上下文注入"))
    lab.setdefault("secondary_class", lab.get("observation_class", lab.get("impact_class", "直接回显型")))
    lab.setdefault("defense_focus", "参数化 / 白名单 / 最小权限")
    lab.setdefault("surfaces", lab.get("tables", []))

LAB_INDEX = {item["slug"]: item for item in LABS}


def get_lab(slug: str):
    return LAB_INDEX[slug]


def _group_by(items: list[dict], key: str, order: list[str]):
    grouped = defaultdict(list)
    for item in items:
        grouped[item[key]].append(item)
    result = []
    for group_name in order:
        if grouped[group_name]:
            result.append({"name": group_name, "labs": grouped[group_name]})
    return result


def build_taxonomy() -> dict:
    return {
        "position_groups": _group_by(LABS, "position_class", POSITION_ORDER),
        "observation_groups": _group_by(LABS, "observation_class", OBSERVATION_ORDER),
        "impact_groups": _group_by(LABS, "impact_class", IMPACT_ORDER),
        "timing_groups": _group_by(LABS, "timing_class", TIMING_ORDER),
        "database_profiles": DATABASE_ORDER,
        "counts": {
            "positions": len({item["position_class"] for item in LABS}),
            "observations": len({item["observation_class"] for item in LABS}),
            "impacts": len({item["impact_class"] for item in LABS}),
            "timings": len({item["timing_class"] for item in LABS}),
        },
    }
