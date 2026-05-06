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


# =====================================================================
# 批次 5：XXE L04-L05 共 2 个新关卡
# =====================================================================

@bp.route('/labs/xxe/parameter-entity-blind', methods=['GET', 'POST'])
def parameter_entity_blind():
    """L04 参数实体盲打：load_dtd=True 时，% 实体可引用外部 DTD（出网到 internal-service）。
    vuln：load_dtd=True，外部 DTD 会被拉取；safe：load_dtd=False，外接 DTD 拒绝。"""
    xml_text = request.form.get('xml_text', '') if request.method == 'POST' else ''
    output = None
    error = None
    parser_log = None
    if xml_text:
        try:
            output = parse_xml(xml_text, safe=current_mode() == 'safe')
            parser_log = '解析成功（如果 vuln + 含外部 DTD，解析器已发起出站请求）'
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('parameter_entity_blind.html', 'parameter-entity-blind',
                      xml_text=xml_text, output=output, error=error, parser_log=parser_log)


@bp.route('/labs/xxe/error-based-disclosure', methods=['GET', 'POST'])
def error_based_disclosure():
    """L05 错误回显抽取：故意构造一个会触发 parser error 的位置去引用 file 实体。
    vuln：把完整 error message 回显；safe：只回显通用错误，且不解析实体。"""
    xml_text = request.form.get('xml_text', '') if request.method == 'POST' else ''
    output = None
    error = None
    if xml_text:
        try:
            output = parse_xml(xml_text, safe=current_mode() == 'safe')
        except Exception as exc:
            if current_mode() == 'vuln':
                # ❌ 完整回显 parser error（包含被实体展开的内容）
                error = f'{type(exc).__name__}: {exc}'
            else:
                # ✅ 只回显通用错误
                error = 'XML 解析失败（详情见服务端日志）'
    secret_path = data_root() / 'xxe-secret.txt'
    return render_lab('error_based_disclosure.html', 'error-based-disclosure',
                      xml_text=xml_text, output=output, error=error, secret_path=secret_path)


def domain_taxonomy():
    return build_taxonomy(), '主轴：实体扩展路径', '实体扩展路径', '外部资源类型'
