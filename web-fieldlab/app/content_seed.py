from __future__ import annotations

XSS_COMMENTS = [
    {"author": "Lin Teacher", "body": "欢迎来到 <strong>Unified FieldLab</strong>，本页默认用于演示输出编码。"},
    {"author": "Ming Analyst", "body": "如果要观察脚本是否执行，优先使用 fieldlab.record(...) 作为课堂回显。"},
]

XSS_PROFILE = {
    "username": "student.demo",
    "status_note": "正在准备跨域漏洞课堂",
    "signature": "<em>Blue team by day, patch team by night.</em>",
}

XSS_BOOKMARKS = [
    {"title": "课堂首页", "url": "https://intranet.fieldlab.local/home"},
    {"title": "应急流程", "url": "https://intranet.fieldlab.local/playbook"},
]

XSS_MARKDOWN_NOTES = [
    {
        "title": "Week-2 Review",
        "body": "## 提醒\n\n- 下周演示 DOM XSS\n- 记得对 `innerHTML` 做对照讲解\n- 学生可以用 `fieldlab.record()` 验证脚本执行",
    }
]

XSS_SVG_SNIPPETS = [
    {
        "title": "safe-badge",
        "svg_markup": "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='52' viewBox='0 0 180 52'><rect width='180' height='52' rx='12' fill='#1f2430'/><text x='90' y='31' text-anchor='middle' fill='#f7d4a0' font-size='18'>FieldLab Badge</text></svg>",
    }
]

XSS_API_CARDS = [
    {"title": "Incident review board", "snippet": "复盘页面会把搜索关键字高亮到 DOM 里。", "tag": "dom"},
    {"title": "Admin quick memo", "snippet": "JSON 接口返回的数据如果直接拼 innerHTML，前端同样会出事。", "tag": "api"},
    {"title": "Client widget", "snippet": "Hash、message、template literal 都可能成为浏览器端 sink。", "tag": "client"},
]

SSTI_TEMPLATES = [
    {"title": "weekly-mail", "body": "<h2>Hello {{ student_name }}</h2><p>Your lab score is {{ score }}.</p>"},
]

SSTI_THEME_SNIPPETS = [
    {"name": "simple-banner", "body": "<section class='preview-banner'><strong>{{ title }}</strong><p>{{ note }}</p></section>"},
]

AUTH_USERS = [
    {"user_id": 1, "username": "alice", "display_name": "Alice Student", "role": "student"},
    {"user_id": 2, "username": "bob", "display_name": "Bob Student", "role": "student"},
    {"user_id": 3, "username": "carol", "display_name": "Carol Teacher", "role": "teacher"},
    {"user_id": 4, "username": "dave", "display_name": "Dave Admin", "role": "admin"},
]

AUTH_ORDERS = [
    {"order_id": 1001, "owner_user_id": 1, "item_name": "Red Team Hoodie", "total_amount": 299.0, "secret_note": "Alice 用作课堂奖品，含隐藏折扣码 A-ROOM."},
    {"order_id": 1002, "owner_user_id": 2, "item_name": "Blue Team Sticker Pack", "total_amount": 49.0, "secret_note": "Bob 的发票联系人是个人邮箱。"},
]

AUTH_NOTES = [
    {"note_id": 2001, "owner_user_id": 1, "body": "Alice 的课后总结：需要多练 DOM sink。"},
    {"note_id": 2002, "owner_user_id": 2, "body": "Bob 的课后总结：对 SQLi 分类法终于顺了。"},
]

AUTH_TICKETS = [
    {"ticket_id": 3001, "owner_user_id": 1, "subject": "Need lab extension", "status": "open", "internal_note": "仅管理员可批准延长时长"},
    {"ticket_id": 3002, "owner_user_id": 2, "subject": "Request score review", "status": "open", "internal_note": "需老师或管理员处理"},
]

UPLOAD_SEEDS = [
    {"lab_slug": "public-html", "original_name": "welcome.txt", "stored_name": "welcome.txt", "declared_type": "text/plain", "stored_path": "uploads/public/welcome.txt", "note": "默认示例文件", "is_public": 1},
]

PAYMENT_PRODUCTS = [
    {"product_id": 1, "name": "Kanxue Hoodie", "price": 299.0, "stock": 20},
    {"product_id": 2, "name": "FieldLab Coins Pack", "price": 99.0, "stock": 50},
]

PAYMENT_WALLETS = [
    {"owner_label": "alice", "balance": 500.0, "credits": 0},
]

PAYMENT_COUPONS = [
    {"code": "WELCOME100", "discount_amount": 100.0, "remaining_uses": 1, "active": 1},
    {"code": "HALF50", "discount_amount": 50.0, "remaining_uses": 2, "active": 1},
]

PAYMENT_ORDERS = [
    {"order_ref": "PAY-10001", "owner_label": "alice", "product_name": "Kanxue Hoodie", "expected_amount": 299.0, "paid_amount": 0.0, "status": "pending", "note": "用于重复回调示例", "callback_count": 0},
]

INJECTION_SNIPPETS = [
    {"title": "default-rule", "body": "result = price * quantity\nsummary = f'price={price}, quantity={quantity}, total={result}'"},
]

XXE_DOCUMENTS = [
    {"title": "invoice-sample", "body": "<?xml version='1.0'?><invoice><customer>Alice</customer><amount>299</amount></invoice>"},
]

JSONP_PROFILES = [
    {"username": "alice", "email": "alice@class.local", "role": "student", "private_note": "FLAG{jsonp_sensitive_profile}"},
    {"username": "bob", "email": "bob@class.local", "role": "student", "private_note": "Bob profile secret"},
]

RACE_COUPONS = [{"code": "RACE-ONCE", "remaining_uses": 1}]
RACE_INVENTORY = [{"sku": "hoodie-one", "stock": 1}]
RACE_WALLETS = [{"owner": "alice", "balance": 40.0}]
RACE_SEATS = [{"event_name": "masterclass-seat", "remaining": 1}]

UPLOAD_BANNER_HTML = "<div class='preview-banner'><strong>Upload Bulletin</strong><p>默认公告：禁止上传可执行脚本。</p></div>"
INJECTION_AUDIT_LOG = """INFO boot complete
INFO scheduler heartbeat ok
WARN user submitted malformed expression once
ERROR coupon callback duplicated in dry-run
"""
XXE_SECRET_TEXT = "FLAG{xxe_reads_local_file}"
