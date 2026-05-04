from __future__ import annotations

import html
from urllib.parse import urlparse

import bleach
import markdown
from flask import Blueprint, jsonify, render_template, request
from markupsafe import Markup

from content_store import execute, query_all, query_one
from shared import current_mode
from xss_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('xss', __name__)

SAFE_TAGS = ['b', 'strong', 'i', 'em', 'code', 'pre', 'p', 'ul', 'ol', 'li', 'blockquote', 'a', 'br', 'span']
SAFE_ATTRS = {'a': ['href', 'title', 'target', 'rel'], 'span': ['class']}
SAFE_PROTOCOLS = ['http', 'https', 'mailto']


def clean_html_fragment(value: str) -> str:
    return bleach.clean(value, tags=SAFE_TAGS, attributes=SAFE_ATTRS, protocols=SAFE_PROTOCOLS, strip=True)


def render_markdown(value: str, safe: bool) -> Markup:
    rendered = markdown.markdown(value, extensions=['extra', 'sane_lists'])
    return Markup(clean_html_fragment(rendered) if safe else rendered)


def sanitize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme:
        return url
    return url if parsed.scheme.lower() in {'http', 'https', 'mailto'} else None


def naive_filter(value: str) -> str:
    filtered = value.replace('<script', '')
    filtered = filtered.replace('</script>', '')
    filtered = filtered.replace('javascript:', '')
    return filtered


def render_lab(template_name: str, slug: str, **context):
    return render_template(
        f'xss/labs/{template_name}',
        lab=get_lab(slug),
        mode=current_mode(),
        show_event_dock=True,
        **context,
    )


def domain_info() -> dict:
    return {
        'code': 'XSS',
        'title': 'XSS 轨道',
        'description': '按反射/存储/DOM/二次路径与浏览器上下文组织跨站脚本关卡。',
        'summary': 'HTML、属性、JS 字符串、Markdown、SVG、协议、srcdoc 全覆盖。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/xss',
        'teaching_points': [
            '先讲上下文，再讲 sink，最后讲传播路径。',
            '把弹窗验证换成 fieldlab.record，课堂更稳定。',
            '重点让学生理解 innerHTML、srcdoc、href、Markdown 渲染器的差异。',
        ],
    }


@bp.route('/api/lab-events', methods=['GET', 'POST', 'DELETE'])
def lab_events():
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        execute('INSERT INTO browser_events (lab_slug, message, source, created_at) VALUES (?, ?, ?, datetime(\'now\'))', (payload.get('lab', 'unknown'), payload.get('message', 'payload executed'), payload.get('source', 'browser')))
        return jsonify({'status': 'stored'})
    if request.method == 'DELETE':
        execute('DELETE FROM browser_events')
        return jsonify({'status': 'cleared'})
    rows = query_all('SELECT event_id, lab_slug, message, source, created_at FROM browser_events ORDER BY event_id DESC LIMIT 12')
    return jsonify({'rows': rows})


@bp.route('/api/cards/search')
def api_cards_search():
    q = request.args.get('q', '')
    needle = f'%{q}%'
    rows = query_all('SELECT card_id, title, snippet, tag FROM xss_api_cards WHERE title LIKE ? OR snippet LIKE ? OR tag LIKE ? ORDER BY card_id', (needle, needle, needle))
    return jsonify({'query': q, 'rows': rows})


@bp.route('/receiver/postmessage')
def receiver_postmessage():
    return render_template('xss/receiver_postmessage.html', mode=current_mode(), show_event_dock=False)


@bp.route('/labs/xss/reflected-html')
def reflected_html():
    message = request.args.get('message', '')
    rendered_message = Markup(message) if message and current_mode() == 'vuln' else message if message else None
    return render_lab('reflected_html.html', 'reflected-html', message=message, rendered_message=rendered_message)


@bp.route('/labs/xss/reflected-attribute')
def reflected_attribute():
    nickname = request.args.get('nickname', '')
    badge_markup = None
    if nickname and current_mode() == 'vuln':
        badge_markup = Markup(f'<button class="demo-badge" title="{nickname}" data-owner="{nickname}">Hover preview badge</button>')
    return render_lab('reflected_attribute.html', 'reflected-attribute', nickname=nickname, badge_markup=badge_markup)


@bp.route('/labs/xss/js-string')
def js_string():
    note = request.args.get('note', '')
    script_block = None
    code_preview = None
    if note and current_mode() == 'vuln':
        code_preview = "const banner = '" + note + "';\\ndocument.getElementById('js-output').innerHTML = banner;"
        script_block = Markup("<script>const banner = '" + note + "';document.getElementById('js-output').innerHTML = banner;</script>")
    elif note:
        code_preview = 'const banner = JSON-safe string;\\ndocument.getElementById(\'js-output\').textContent = banner;'
    return render_lab('js_string.html', 'js-string', note=note, script_block=script_block, code_preview=code_preview)


@bp.route('/labs/xss/stored-comments', methods=['GET', 'POST'])
def stored_comments():
    if request.method == 'POST':
        execute('INSERT INTO xss_comments (author, body, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('author', 'Anonymous')[:40], request.form.get('body', '')))
    rows = query_all('SELECT comment_id, author, body, created_at FROM xss_comments ORDER BY comment_id DESC')
    comments = [{**row, 'body_rendered': Markup(row['body']) if current_mode() == 'vuln' else Markup(clean_html_fragment(row['body']))} for row in rows]
    return render_lab('stored_comments.html', 'stored-comments', comments=comments)


@bp.route('/labs/xss/second-order-signature', methods=['GET', 'POST'])
def second_order_signature():
    message = None
    review_mode = False
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            execute('UPDATE xss_profiles SET status_note = ?, signature = ?, updated_at = datetime(\'now\') WHERE profile_id = 1', (request.form.get('status_note', ''), request.form.get('signature', '')))
            message = '签名档已保存。下一步请切到管理员摘要区触发二次渲染。'
        elif action == 'review':
            review_mode = True
    profile = query_one('SELECT username, status_note, signature, updated_at FROM xss_profiles WHERE profile_id = 1')
    admin_signature = Markup(profile['signature']) if review_mode and current_mode() == 'vuln' else Markup(clean_html_fragment(profile['signature'])) if review_mode else None
    return render_lab('second_order_signature.html', 'second-order-signature', profile=profile, message=message, review_mode=review_mode, admin_signature=admin_signature)


@bp.route('/labs/xss/dom-hash')
def dom_hash():
    return render_lab('dom_hash.html', 'dom-hash')


@bp.route('/labs/xss/dom-api-template')
def dom_api_template():
    return render_lab('dom_api_template.html', 'dom-api-template')


@bp.route('/labs/xss/postmessage-srcdoc')
def postmessage_srcdoc():
    return render_lab('postmessage_srcdoc.html', 'postmessage-srcdoc')


@bp.route('/labs/xss/markdown-preview', methods=['GET', 'POST'])
def markdown_preview():
    if request.method == 'POST':
        execute('INSERT INTO xss_markdown_notes (title, body, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled')[:80], request.form.get('body', '')))
    rows = query_all('SELECT note_id, title, body, created_at FROM xss_markdown_notes ORDER BY note_id DESC LIMIT 6')
    notes = [{**row, 'rendered': render_markdown(row['body'], safe=current_mode() == 'safe')} for row in rows]
    return render_lab('markdown_preview.html', 'markdown-preview', notes=notes)


@bp.route('/labs/xss/svg-preview', methods=['GET', 'POST'])
def svg_preview():
    if request.method == 'POST':
        execute('INSERT INTO xss_svg_snippets (title, svg_markup, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled badge')[:80], request.form.get('svg_markup', '')))
    rows = query_all('SELECT snippet_id, title, svg_markup, created_at FROM xss_svg_snippets ORDER BY snippet_id DESC LIMIT 6')
    snippets = [{**row, 'rendered': Markup(row['svg_markup']) if current_mode() == 'vuln' else row['svg_markup']} for row in rows]
    return render_lab('svg_preview.html', 'svg-preview', snippets=snippets)


@bp.route('/labs/xss/url-bookmarks', methods=['GET', 'POST'])
def url_bookmarks():
    if request.method == 'POST':
        execute('INSERT INTO xss_bookmarks (title, url, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled')[:80], request.form.get('url', '')[:500]))
    rows = query_all('SELECT bookmark_id, title, url, created_at FROM xss_bookmarks ORDER BY bookmark_id DESC')
    bookmarks = [{**row, 'safe_url': sanitize_url(row['url']) if current_mode() == 'safe' else row['url']} for row in rows]
    return render_lab('url_bookmarks.html', 'url-bookmarks', bookmarks=bookmarks)


@bp.route('/labs/xss/faux-fix')
def faux_fix():
    payload = request.args.get('payload', '')
    filtered_payload = None
    rendered_payload = None
    if payload:
        if current_mode() == 'vuln':
            filtered_payload = naive_filter(payload)
            rendered_payload = Markup(filtered_payload)
        else:
            filtered_payload = payload
            rendered_payload = payload
    return render_lab('faux_fix.html', 'faux-fix', payload=payload, filtered_payload=filtered_payload, rendered_payload=rendered_payload)


def domain_taxonomy():
    taxonomy = build_taxonomy()
    return taxonomy['context_groups'], '主轴：浏览器上下文', '浏览器上下文', '关键 sink'
