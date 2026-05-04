from __future__ import annotations

from lxml import etree
from flask import Blueprint, render_template, request

from content_store import data_root, execute, query_all, query_one
from shared import current_mode
from xxe_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('xxe', __name__)


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'xxe/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, **context)


def domain_info() -> dict:
    return {
        'code': 'XXE',
        'title': 'XXE 轨道',
        'description': '围绕 XML 外部实体的本地文件读取、内网请求和存储后二次解析。',
        'summary': '把“解析器配置”讲成第一性问题，而不是字符串替换问题。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/xxe',
        'teaching_points': [
            '先讲实体解析会让 XML 输入延伸到文件系统和网络。',
            '再把 XXE 和 SSRF 串联起来。',
            '最后讲存储后二次解析。',
        ],
    }


def parse_xml(xml_text: str, safe: bool) -> str:
    parser = etree.XMLParser(resolve_entities=not safe, load_dtd=not safe, no_network=safe, huge_tree=True)
    root = etree.fromstring(xml_text.encode(), parser=parser)
    return ''.join(root.itertext()).strip() or etree.tostring(root, pretty_print=True, encoding='unicode')


@bp.route('/labs/xxe/local-file', methods=['GET', 'POST'])
def local_file():
    xml_text = request.form.get('xml_text', '') if request.method == 'POST' else ''
    output = None
    error = None
    if xml_text:
        try:
            output = parse_xml(xml_text, safe=current_mode() == 'safe')
        except Exception as exc:
            error = str(exc)
    secret_path = data_root() / 'xxe-secret.txt'
    return render_lab('local_file.html', 'local-file', xml_text=xml_text, output=output, error=error, secret_path=secret_path)


@bp.route('/labs/xxe/internal-ssrf', methods=['GET', 'POST'])
def internal_ssrf():
    xml_text = request.form.get('xml_text', '') if request.method == 'POST' else ''
    output = None
    error = None
    if xml_text:
        try:
            output = parse_xml(xml_text, safe=current_mode() == 'safe')
        except Exception as exc:
            error = str(exc)
    return render_lab('internal_ssrf.html', 'internal-ssrf', xml_text=xml_text, output=output, error=error)


@bp.route('/labs/xxe/stored-xml', methods=['GET', 'POST'])
def stored_xml():
    output = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            execute('INSERT INTO xxe_documents (title, body, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled')[:80], request.form.get('body', '')))
        elif action == 'preview':
            row = query_one('SELECT * FROM xxe_documents ORDER BY doc_id DESC LIMIT 1')
            if row:
                try:
                    output = parse_xml(row['body'], safe=current_mode() == 'safe')
                except Exception as exc:
                    error = str(exc)
    docs = query_all('SELECT * FROM xxe_documents ORDER BY doc_id DESC LIMIT 6')
    return render_lab('stored_xml.html', 'stored-xml', docs=docs, output=output, error=error)


def domain_taxonomy():
    return build_taxonomy(), '主轴：实体扩展路径', '实体扩展路径', '外部资源类型'
