from __future__ import annotations

SEED_COMMENTS = [
    {"author": "Lin Teacher", "body": "欢迎来到 <strong>XSS FieldLab</strong>，本页默认用于演示输出编码。"},
    {"author": "Ming Analyst", "body": "如果要观察脚本是否执行，优先使用 fieldlab.record(...) 作为课堂回显。"},
]

SEED_PROFILE = {
    "username": "student.demo",
    "status_note": "正在准备课件预演",
    "signature": "<em>Blue team by day, patch team by night.</em>",
}

SEED_BOOKMARKS = [
    {"title": "课堂首页", "url": "https://intranet.fieldlab.local/home"},
    {"title": "应急流程", "url": "https://intranet.fieldlab.local/playbook"},
]

SEED_MARKDOWN_NOTES = [
    {
        "title": "Week-2 Review",
        "body": "## 提醒\n\n- 下周演示 DOM XSS\n- 记得对 `innerHTML` 做对照讲解\n- 学生可以用 `fieldlab.record()` 验证脚本执行",
    }
]

SEED_SVG_SNIPPETS = [
    {
        "title": "safe-badge",
        "svg_markup": "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='52' viewBox='0 0 180 52'><rect width='180' height='52' rx='12' fill='#1f2430'/><text x='90' y='31' text-anchor='middle' fill='#f7d4a0' font-size='18'>FieldLab Badge</text></svg>",
    }
]

SEED_API_CARDS = [
    {"title": "Incident review board", "snippet": "复盘页面会把搜索关键字高亮到 DOM 里。", "tag": "dom"},
    {"title": "Admin quick memo", "snippet": "JSON 接口返回的数据如果直接拼 innerHTML，前端同样会出事。", "tag": "api"},
    {"title": "Client widget", "snippet": "Hash、message、template literal 都可能成为浏览器端 sink。", "tag": "client"},
]
