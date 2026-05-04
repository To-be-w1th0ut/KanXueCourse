from __future__ import annotations

import html
from urllib.parse import urlparse

import bleach
import markdown
from flask import Flask, jsonify, render_template, request
from markupsafe import Markup

from config import Config
from labs import LABS, build_taxonomy, get_lab
from storage import execute, init_db, query_all, query_one

app = Flask(__name__)
app.config.from_object(Config)
init_db(force=False)

SAFE_TAGS = [
    "b",
    "strong",
    "i",
    "em",
    "code",
    "pre",
    "p",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "br",
    "span",
]
SAFE_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
}
SAFE_PROTOCOLS = ["http", "https", "mailto"]


@app.context_processor
def inject_globals():
    return {"all_labs": LABS, "app_public_port": Config.APP_PUBLIC_PORT}


def current_mode() -> str:
    return "safe" if request.args.get("mode") == "safe" else "vuln"


def render_lab(template_name: str, slug: str, **context):
    return render_template(template_name, lab=get_lab(slug), mode=current_mode(), **context)


def clean_html_fragment(value: str) -> str:
    return bleach.clean(
        value,
        tags=SAFE_TAGS,
        attributes=SAFE_ATTRS,
        protocols=SAFE_PROTOCOLS,
        strip=True,
    )


def render_markdown(value: str, safe: bool) -> Markup:
    rendered = markdown.markdown(value, extensions=["extra", "sane_lists"])
    if safe:
        return Markup(clean_html_fragment(rendered))
    return Markup(rendered)


def sanitize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme:
        return url
    if parsed.scheme.lower() in {"http", "https", "mailto"}:
        return url
    return None


def naive_filter(value: str) -> str:
    filtered = value.replace("<script", "")
    filtered = filtered.replace("</script>", "")
    filtered = filtered.replace("javascript:", "")
    return filtered


@app.route("/")
def index():
    taxonomy = build_taxonomy()
    return render_template("index.html", labs=LABS, taxonomy=taxonomy)


@app.route("/labs")
def labs_view():
    taxonomy = build_taxonomy()
    return render_template("lab_list.html", labs=LABS, taxonomy=taxonomy)


@app.route("/healthz")
def healthz():
    try:
        query_one("SELECT 1 AS ok")
        return jsonify({"status": "ok", "db": 1})
    except Exception as exc:  # pragma: no cover
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/lab-events", methods=["GET", "POST", "DELETE"])
def lab_events():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        execute(
            "INSERT INTO lab_events (lab_slug, message, source, created_at) VALUES (?, ?, ?, datetime('now'))",
            (
                payload.get("lab", "unknown"),
                payload.get("message", "payload executed"),
                payload.get("source", "browser"),
            ),
        )
        return jsonify({"status": "stored"})
    if request.method == "DELETE":
        execute("DELETE FROM lab_events")
        return jsonify({"status": "cleared"})
    rows = query_all(
        "SELECT event_id, lab_slug, message, source, created_at FROM lab_events ORDER BY event_id DESC LIMIT 12"
    )
    return jsonify({"rows": rows})


@app.route("/api/cards/search")
def api_cards_search():
    q = request.args.get("q", "")
    needle = f"%{q}%"
    rows = query_all(
        "SELECT card_id, title, snippet, tag FROM api_cards WHERE title LIKE ? OR snippet LIKE ? OR tag LIKE ? ORDER BY card_id",
        (needle, needle, needle),
    )
    return jsonify({"query": q, "rows": rows})


@app.route("/labs/reflected-html")
def reflected_html():
    message = request.args.get("message", "")
    rendered_message = None
    if message:
        rendered_message = Markup(message) if current_mode() == "vuln" else message
    return render_lab(
        "labs/reflected_html.html",
        "reflected-html",
        message=message,
        rendered_message=rendered_message,
    )


@app.route("/labs/reflected-attribute")
def reflected_attribute():
    nickname = request.args.get("nickname", "")
    badge_markup = None
    if nickname and current_mode() == "vuln":
        badge_markup = Markup(
            f'<button class="demo-badge" title="{nickname}" data-owner="{nickname}">Hover preview badge</button>'
        )
    return render_lab(
        "labs/reflected_attribute.html",
        "reflected-attribute",
        nickname=nickname,
        badge_markup=badge_markup,
    )


@app.route("/labs/js-string")
def js_string():
    note = request.args.get("note", "")
    script_block = None
    code_preview = None
    if note and current_mode() == "vuln":
        code_preview = (
            "const banner = '"
            + note
            + "';\ndocument.getElementById('js-output').innerHTML = banner;"
        )
        script_block = Markup(
            "<script>const banner = '"
            + note
            + "';document.getElementById('js-output').innerHTML = banner;</script>"
        )
    elif note:
        code_preview = "const banner = JSON-safe string;\ndocument.getElementById('js-output').textContent = banner;"
    return render_lab(
        "labs/js_string.html",
        "js-string",
        note=note,
        script_block=script_block,
        code_preview=code_preview,
    )


@app.route("/labs/stored-comments", methods=["GET", "POST"])
def stored_comments():
    if request.method == "POST":
        author = request.form.get("author", "Anonymous")[:40]
        body = request.form.get("body", "")
        execute(
            "INSERT INTO comments (author, body, created_at) VALUES (?, ?, datetime('now'))",
            (author, body),
        )
    rows = query_all("SELECT comment_id, author, body, created_at FROM comments ORDER BY comment_id DESC")
    comments = []
    for row in rows:
        comments.append(
            {
                **row,
                "body_rendered": Markup(row["body"]) if current_mode() == "vuln" else Markup(clean_html_fragment(row["body"])),
            }
        )
    return render_lab("labs/stored_comments.html", "stored-comments", comments=comments)


@app.route("/labs/second-order-signature", methods=["GET", "POST"])
def second_order_signature():
    message = None
    review_mode = False
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            signature = request.form.get("signature", "")
            status_note = request.form.get("status_note", "")
            execute(
                "UPDATE profiles SET status_note = ?, signature = ?, updated_at = datetime('now') WHERE profile_id = 1",
                (status_note, signature),
            )
            message = "签名档已保存。下一步请切到管理员摘要区触发二次渲染。"
        elif action == "review":
            review_mode = True
    profile = query_one("SELECT username, status_note, signature, updated_at FROM profiles WHERE profile_id = 1")
    admin_signature = None
    if review_mode:
        admin_signature = Markup(profile["signature"]) if current_mode() == "vuln" else Markup(clean_html_fragment(profile["signature"]))
    return render_lab(
        "labs/second_order_signature.html",
        "second-order-signature",
        profile=profile,
        message=message,
        review_mode=review_mode,
        admin_signature=admin_signature,
    )


@app.route("/labs/dom-hash")
def dom_hash():
    return render_lab("labs/dom_hash.html", "dom-hash")


@app.route("/labs/dom-api-template")
def dom_api_template():
    return render_lab("labs/dom_api_template.html", "dom-api-template")


@app.route("/labs/postmessage-srcdoc")
def postmessage_srcdoc():
    return render_lab("labs/postmessage_srcdoc.html", "postmessage-srcdoc")


@app.route("/receiver/postmessage")
def receiver_postmessage():
    return render_template("receiver_postmessage.html", mode=current_mode())


@app.route("/labs/markdown-preview", methods=["GET", "POST"])
def markdown_preview():
    if request.method == "POST":
        execute(
            "INSERT INTO markdown_notes (title, body, created_at) VALUES (?, ?, datetime('now'))",
            (request.form.get("title", "Untitled")[:80], request.form.get("body", "")),
        )
    rows = query_all("SELECT note_id, title, body, created_at FROM markdown_notes ORDER BY note_id DESC LIMIT 6")
    notes = []
    for row in rows:
        notes.append({**row, "rendered": render_markdown(row["body"], safe=current_mode() == "safe")})
    return render_lab("labs/markdown_preview.html", "markdown-preview", notes=notes)


@app.route("/labs/svg-preview", methods=["GET", "POST"])
def svg_preview():
    if request.method == "POST":
        execute(
            "INSERT INTO svg_snippets (title, svg_markup, created_at) VALUES (?, ?, datetime('now'))",
            (request.form.get("title", "Untitled badge")[:80], request.form.get("svg_markup", "")),
        )
    rows = query_all("SELECT snippet_id, title, svg_markup, created_at FROM svg_snippets ORDER BY snippet_id DESC LIMIT 6")
    snippets = []
    for row in rows:
        snippets.append(
            {
                **row,
                "rendered": Markup(row["svg_markup"]) if current_mode() == "vuln" else row["svg_markup"],
            }
        )
    return render_lab("labs/svg_preview.html", "svg-preview", snippets=snippets)


@app.route("/labs/url-bookmarks", methods=["GET", "POST"])
def url_bookmarks():
    if request.method == "POST":
        execute(
            "INSERT INTO bookmarks (title, url, created_at) VALUES (?, ?, datetime('now'))",
            (request.form.get("title", "Untitled")[:80], request.form.get("url", "")[:500]),
        )
    rows = query_all("SELECT bookmark_id, title, url, created_at FROM bookmarks ORDER BY bookmark_id DESC")
    bookmarks = []
    for row in rows:
        safe_url = sanitize_url(row["url"]) if current_mode() == "safe" else row["url"]
        bookmarks.append({**row, "safe_url": safe_url})
    return render_lab("labs/url_bookmarks.html", "url-bookmarks", bookmarks=bookmarks)


@app.route("/labs/faux-fix")
def faux_fix():
    payload = request.args.get("payload", "")
    filtered_payload = None
    rendered_payload = None
    if payload:
        if current_mode() == "vuln":
            filtered_payload = naive_filter(payload)
            rendered_payload = Markup(filtered_payload)
        else:
            filtered_payload = payload
            rendered_payload = payload
    return render_lab(
        "labs/faux_fix.html",
        "faux-fix",
        payload=payload,
        filtered_payload=filtered_payload,
        rendered_payload=rendered_payload,
    )


if __name__ == "__main__":
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=False)
