from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, make_response, render_template, request
from sqlalchemy import text

from shared import current_mode
from sqli_db import engine, get_cursor, run_multi_statement, run_select, run_statement
from sqli_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('sqli', __name__)


def render_lab(template_name: str, slug: str, **context):
    return render_template(
        f'sqli/labs/{template_name}',
        lab=get_lab(slug),
        mode=current_mode(),
        show_event_dock=False,
        **context,
    )


def domain_info() -> dict:
    return {
        'code': 'SQLI',
        'title': 'SQL Injection 轨道',
        'description': '按注入位置、回显方式和业务影响讲清 SQL 注入。',
        'summary': '参数化、白名单、多语句、二次注入、ORM 误用全覆盖。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/sqli',
        'teaching_points': [
            '先按注入位置讲值位 / 结构位 / 语句级 / 动态 SQL。',
            '再讲回显方式：直接回显、报错、布尔盲注、时间盲注。',
            '最后回收到修复：参数化 + 白名单 + 最小权限。',
        ],
    }


@bp.route('/labs/sqli/login-bypass', methods=['GET', 'POST'])
def login_bypass():
    matched_user = None
    result = None
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        try:
            if current_mode() == 'safe':
                rows = run_select(
                    'SELECT username, role, display_name, department FROM users WHERE username = %s AND password = %s LIMIT 1',
                    (username, password),
                )
            else:
                sql = (
                    'SELECT username, role, display_name, department FROM users '
                    f"WHERE username = '{username}' AND password = '{password}' LIMIT 1"
                )
                rows = run_select(sql)
            matched_user = rows[0] if rows else None
            result = '登录成功' if rows else '登录失败'
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '请求处理失败。'
    return render_lab('login_bypass.html', 'login-bypass', matched_user=matched_user, result=result, error=error)


@bp.route('/labs/sqli/product-union')
def product_union():
    q = request.args.get('q', '')
    rows = []
    error = None
    if q:
        try:
            if current_mode() == 'safe':
                needle = f'%{q}%'
                rows = run_select(
                    'SELECT product_id, sku, name, price, category FROM products WHERE name LIKE %s OR description LIKE %s LIMIT 8',
                    (needle, needle),
                )
            else:
                sql = (
                    'SELECT product_id, sku, name, price, category FROM products '
                    f"WHERE name LIKE '%{q}%' OR description LIKE '%{q}%' LIMIT 8"
                )
                rows = run_select(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '搜索请求无效。'
    return render_lab('product_union.html', 'product-union', rows=rows, q=q, error=error)


@bp.route('/labs/sqli/error-ticket')
def error_ticket():
    ticket_id = request.args.get('id', '1')
    rows = []
    error = None
    if ticket_id:
        try:
            if current_mode() == 'safe':
                rows = run_select(
                    'SELECT ticket_id, title, status, owner_email, severity FROM support_tickets WHERE ticket_id = %s',
                    (int(ticket_id),),
                )
            else:
                sql = (
                    'SELECT ticket_id, title, status, owner_email, internal_note, severity '
                    f'FROM support_tickets WHERE ticket_id = {ticket_id}'
                )
                rows = run_select(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '参数非法，详细错误已隐藏。'
    return render_lab('error_ticket.html', 'error-ticket', ticket_id=ticket_id, rows=rows, error=error)


@bp.route('/labs/sqli/employee-blind')
def employee_blind():
    badge = request.args.get('badge', '')
    exists = None
    if badge:
        if current_mode() == 'safe':
            rows = run_select('SELECT employee_id FROM employees WHERE badge_code = %s AND active = 1 LIMIT 1', (badge,))
        else:
            sql = 'SELECT employee_id FROM employees ' + f"WHERE badge_code = '{badge}' AND active = 1 LIMIT 1"
            rows = run_select(sql)
        exists = bool(rows)
    return render_lab('employee_blind.html', 'employee-blind', badge=badge, exists=exists)


@bp.route('/labs/sqli/shipping-time')
def shipping_time():
    order_number = request.args.get('order', '')
    status = None
    elapsed = None
    error = None
    if order_number:
        start = time.perf_counter()
        try:
            if current_mode() == 'safe':
                rows = run_select('SELECT status FROM orders WHERE order_number = %s LIMIT 1', (order_number,))
            else:
                rows = run_select(f"SELECT status FROM orders WHERE order_number = '{order_number}' LIMIT 1")
            status = rows[0]['status'] if rows else '未找到对应订单或结果被抑制'
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '请求被拒绝。'
        finally:
            elapsed = round(time.perf_counter() - start, 3)
    return render_lab('shipping_time.html', 'shipping-time', order_number=order_number, status=status, elapsed=elapsed, error=error)


@bp.route('/labs/sqli/report-stacked')
def report_stacked():
    month = request.args.get('month', '2026-04')
    rows = []
    message = None
    error = None
    try:
        if current_mode() == 'safe':
            rows = run_select(
                'SELECT log_id, actor, action, source_ip, created_at FROM audit_logs WHERE action_month = %s ORDER BY created_at DESC LIMIT 15',
                (month,),
            )
        else:
            sql = (
                'SELECT log_id, actor, action, source_ip, created_at FROM audit_logs '
                f"WHERE action_month = '{month}' ORDER BY created_at DESC LIMIT 15;"
            )
            result_sets = run_multi_statement(sql)
            first = result_sets[0] if result_sets else []
            rows = first if isinstance(first, list) else []
            if len(result_sets) > 1:
                message = f'本次请求额外执行了 {len(result_sets) - 1} 条后续语句。'
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '参数不符合报表规范。'
    sample_grades = run_select('SELECT student_no, student_name, final_score, teacher_comment FROM grades ORDER BY student_no LIMIT 5')
    return render_lab('report_stacked.html', 'report-stacked', month=month, rows=rows, message=message, error=error, sample_grades=sample_grades)


@bp.route('/labs/sqli/second-order', methods=['GET', 'POST'])
def second_order():
    save_message = None
    report_rows = []
    current_filter = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            filter_name = request.form.get('filter_name', '')
            department_filter = request.form.get('department_filter', '')
            run_statement('INSERT INTO saved_filters (user_id, filter_name, department_filter) VALUES (%s, %s, %s)', (1, filter_name, department_filter))
            save_message = '筛选器已保存。现在请到下方报表区触发它。'
        elif action == 'run':
            saved = run_select('SELECT filter_name, department_filter FROM saved_filters WHERE user_id = 1 ORDER BY filter_id DESC LIMIT 1')
            if saved:
                current_filter = saved[0]['department_filter']
                try:
                    if current_mode() == 'safe':
                        report_rows = run_select('SELECT employee_id, full_name, department, title FROM employees WHERE department = %s ORDER BY full_name', (current_filter,))
                    else:
                        sql = 'SELECT employee_id, full_name, department, title FROM employees ' + f"WHERE department = '{current_filter}' ORDER BY full_name"
                        report_rows = run_select(sql)
                except Exception as exc:
                    error = str(exc) if current_mode() == 'vuln' else '报表筛选值非法。'
    saved_filters = run_select('SELECT filter_id, filter_name, department_filter, created_at FROM saved_filters WHERE user_id = 1 ORDER BY filter_id DESC LIMIT 5')
    return render_lab('second_order.html', 'second-order', save_message=save_message, report_rows=report_rows, current_filter=current_filter, saved_filters=saved_filters, error=error)


@bp.route('/labs/sqli/leaderboard-sort')
def leaderboard_sort():
    sort = request.args.get('sort', 'final_score')
    direction = request.args.get('dir', 'DESC')
    limit = request.args.get('limit', '5')
    rows = []
    error = None
    try:
        if current_mode() == 'safe':
            allowed_sort = {'student_no', 'student_name', 'class_name', 'final_score'}
            allowed_dir = {'ASC', 'DESC'}
            sort = sort if sort in allowed_sort else 'final_score'
            direction = direction.upper() if direction.upper() in allowed_dir else 'DESC'
            parsed_limit = max(1, min(int(limit), 20))
            rows = run_select(
                'SELECT student_no, student_name, class_name, final_score FROM grades ' + f'ORDER BY {sort} {direction} LIMIT {parsed_limit}'
            )
        else:
            rows = run_select(
                'SELECT student_no, student_name, class_name, final_score FROM grades ' + f'ORDER BY {sort} {direction} LIMIT {limit}'
            )
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '排序参数不合法。'
    return render_lab('leaderboard_sort.html', 'leaderboard-sort', rows=rows, sort=sort, direction=direction, limit=limit, error=error)


@bp.route('/labs/sqli/grade-editor', methods=['GET', 'POST'])
def grade_editor():
    affected_rows = None
    error = None
    if request.method == 'POST':
        student_no = request.form.get('student_no', '')
        bonus_expr = request.form.get('bonus_expr', '0')
        remark = request.form.get('remark', '')
        try:
            if current_mode() == 'safe':
                bonus_value = int(bonus_expr)
                if bonus_value < 0 or bonus_value > 15:
                    raise ValueError('补分范围必须在 0 到 15 之间')
                affected_rows = run_statement(
                    'UPDATE grades SET final_score = final_score + %s, teacher_comment = %s WHERE student_no = %s',
                    (bonus_value, remark[:80], student_no),
                )
            else:
                sql = 'UPDATE grades SET final_score = final_score + ' + f"{bonus_expr}, teacher_comment = '{remark}' WHERE student_no = '{student_no}'"
                affected_rows = run_statement(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '更新请求不符合规则。'
    grades = run_select('SELECT student_no, student_name, class_name, midterm, final_exam, final_score, teacher_comment FROM grades ORDER BY student_no')
    return render_lab('grade_editor.html', 'grade-editor', grades=grades, affected_rows=affected_rows, error=error)


@bp.route('/labs/sqli/api-json-sqli')
def api_json_sqli():
    return render_lab('api_json_sqli.html', 'api-json-sqli')


@bp.route('/api/v1/orders/search', methods=['POST'])
def api_orders_search():
    mode = current_mode()
    payload = request.get_json(silent=True) or {}
    customer = payload.get('customer', '')
    min_total = str(payload.get('min_total', '0'))
    try:
        if mode == 'safe':
            amount = Decimal(min_total)
            needle = f'%{customer}%'
            rows = run_select(
                'SELECT order_number, customer_name, total_amount, status FROM orders WHERE customer_name LIKE %s AND total_amount >= %s ORDER BY total_amount DESC LIMIT 10',
                (needle, amount),
            )
        else:
            sql = (
                'SELECT order_number, customer_name, total_amount, status FROM orders '
                f"WHERE customer_name LIKE '%{customer}%' AND total_amount >= {min_total} ORDER BY total_amount DESC LIMIT 10"
            )
            rows = run_select(sql)
        return jsonify({'mode': mode, 'count': len(rows), 'rows': rows})
    except (InvalidOperation, ValueError):
        return jsonify({'mode': mode, 'error': 'min_total 必须是数值。'}), 400
    except Exception as exc:
        return jsonify({'mode': mode, 'error': str(exc) if mode == 'vuln' else '请求格式错误。'}), 400


@bp.route('/labs/sqli/faux-fix', methods=['GET', 'POST'])
def faux_fix():
    matched_user = None
    result = None
    error = None
    def weak_filter(value: str) -> str:
        sanitized = value
        for token in ['union', 'select', ' or ', 'OR', '--', ';']:
            sanitized = sanitized.replace(token, '')
        return sanitized
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        try:
            if current_mode() == 'safe':
                rows = run_select('SELECT username, role, display_name FROM users WHERE username = %s AND password = %s LIMIT 1', (username, password))
            else:
                sql = 'SELECT username, role, display_name FROM users ' + f"WHERE username = '{weak_filter(username)}' AND password = '{weak_filter(password)}' LIMIT 1"
                rows = run_select(sql)
            result = '登录成功' if rows else '登录失败'
            matched_user = rows[0] if rows else None
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '请求处理失败。'
    return render_lab('faux_fix.html', 'faux-fix', matched_user=matched_user, result=result, error=error)


@bp.route('/labs/sqli/orm-misuse')
def orm_misuse():
    category = request.args.get('category', 'Hardware')
    rows = []
    error = None
    try:
        with engine.connect() as connection:
            if current_mode() == 'safe':
                query = text('SELECT product_id, sku, name, category, price FROM products WHERE category = :category ORDER BY price DESC')
                result = connection.execute(query, {'category': category})
            else:
                query = text('SELECT product_id, sku, name, category, price FROM products ' + f"WHERE category = '{category}' ORDER BY price DESC")
                result = connection.execute(query)
            rows = [dict(row._mapping) for row in result]
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '查询参数不合法。'
    return render_lab('orm_misuse.html', 'orm-misuse', rows=rows, category=category, error=error)


# =====================================================================
# SQLi 扩充关卡（L13-L22）
# =====================================================================

LAB_FILE_OUTPUT_DIR = '/tmp/lab'  # 容器内沙箱写入目录


# ---------- L13 INSERT 注入：注册接口 ----------
@bp.route('/labs/sqli/insert-register', methods=['GET', 'POST'])
def insert_register():
    """教学：把 invite_source 字段做字符串拼接进 INSERT VALUES。"""
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        invite_source = request.form.get('invite_source', 'public')
        try:
            if current_mode() == 'safe':
                # ✅ 全部参数化绑定 + 长度截断
                run_statement(
                    'INSERT INTO register_users (username, email, invite_source) VALUES (%s, %s, %s)',
                    (username[:80], email[:160], invite_source[:120]),
                )
            else:
                # ❌ invite_source 直接拼接，VALUES 闭合后可追加任意行
                sql = (
                    "INSERT INTO register_users (username, email, invite_source) "
                    f"VALUES ('{username}', '{email}', '{invite_source}')"
                )
                run_statement(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '注册请求不合法。'
    last_inserted = run_select(
        'SELECT register_id, username, email, role, invite_source, created_at '
        'FROM register_users ORDER BY register_id DESC LIMIT 8'
    )
    return render_lab(
        'insert_register.html', 'insert-register',
        last_inserted=last_inserted, error=error,
    )


# ---------- L14 DELETE 注入：清理任务 ----------
@bp.route('/labs/sqli/delete-cleanup', methods=['GET', 'POST'])
def delete_cleanup():
    """教学：DELETE WHERE expire_token = '<input>' 拼接，可被恒真条件清空全表。"""
    affected = None
    error = None
    if request.method == 'POST':
        token = request.form.get('expire_token', '')
        try:
            if current_mode() == 'safe':
                # ✅ 参数化 + 严格校验 token 格式
                if not token or len(token) > 80:
                    raise ValueError('token 不合法')
                affected = run_statement(
                    'DELETE FROM cleanup_jobs WHERE expire_token = %s',
                    (token,),
                )
            else:
                # ❌ 直接拼接，OR '1'='1' 可让 WHERE 恒真
                sql = f"DELETE FROM cleanup_jobs WHERE expire_token = '{token}'"
                affected = run_statement(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '清理请求不合法。'
    jobs = run_select(
        'SELECT job_id, target_table, expire_token, operator, note '
        'FROM cleanup_jobs ORDER BY job_id'
    )
    return render_lab(
        'delete_cleanup.html', 'delete-cleanup',
        jobs=jobs, affected=affected, error=error,
    )


# ---------- L15 Header 注入：User-Agent 审计 ----------
@bp.route('/labs/sqli/header-audit')
def header_audit():
    """教学：把 User-Agent 直接拼进 INSERT 与 SELECT。"""
    ua = request.headers.get('User-Agent', '')
    error = None
    rows = []
    try:
        if current_mode() == 'safe':
            # ✅ 参数化插入 + 参数化查询
            run_statement(
                'INSERT INTO audit_access_logs (visitor_ua, visit_path) VALUES (%s, %s)',
                (ua[:255], request.path[:255]),
            )
            rows = run_select(
                'SELECT access_id, visitor_ua, visit_path, visit_at '
                'FROM audit_access_logs WHERE visitor_ua = %s '
                'ORDER BY access_id DESC LIMIT 10',
                (ua,),
            )
        else:
            # ❌ INSERT 用参数化（保证写入成功），SELECT WHERE 仍直接拼接 → 注入点
            run_statement(
                'INSERT INTO audit_access_logs (visitor_ua, visit_path) VALUES (%s, %s)',
                (ua[:255], request.path[:255]),
            )
            rows = run_select(
                'SELECT access_id, visitor_ua, visit_path, visit_at '
                'FROM audit_access_logs '
                f"WHERE visitor_ua = '{ua}' "
                'ORDER BY access_id DESC LIMIT 10'
            )
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '审计请求不合法。'
    return render_lab(
        'header_audit.html', 'header-audit',
        rows=rows, ua=ua, error=error,
    )


# ---------- L16 Cookie 注入：主题偏好 ----------
@bp.route('/labs/sqli/cookie-theme')
def cookie_theme():
    """教学：Cookie `theme` 直接进入 WHERE，is_active=1 限制可被 OR 绕过。"""
    theme_code = request.cookies.get('theme', 'aurora')
    rows = []
    error = None
    try:
        if current_mode() == 'safe':
            # ✅ cookie 严格校验 + 参数绑定 + 强制 is_active=1
            allow = {'aurora', 'amber'}
            theme_code_safe = theme_code if theme_code in allow else 'aurora'
            rows = run_select(
                'SELECT theme_code, theme_label FROM theme_preferences '
                'WHERE theme_code = %s AND is_active = 1',
                (theme_code_safe,),
            )
        else:
            # ❌ cookie 直接拼接进 SQL
            sql = (
                "SELECT theme_code, theme_label, is_active FROM theme_preferences "
                f"WHERE theme_code = '{theme_code}' AND is_active = 1"
            )
            rows = run_select(sql)
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '主题请求不合法。'
    response = make_response(render_lab(
        'cookie_theme.html', 'cookie-theme',
        rows=rows, theme_code=theme_code, error=error,
    ))
    if 'theme' not in request.cookies:
        response.set_cookie('theme', 'aurora', max_age=3600)
    return response


# ---------- L17 宽字节注入 ----------
def _addslashes(value: str) -> str:
    """模拟旧版 PHP addslashes：把 ' " \\ NUL 前面加反斜杠。"""
    out = []
    for ch in value:
        if ch in ("'", '"', '\\', '\x00'):
            out.append('\\')
        out.append(ch)
    return ''.join(out)


@bp.route('/labs/sqli/wide-byte')
def wide_byte():
    """教学：addslashes 在 GBK 表中失效。

    payload 范例：keyword=%bf%27 UNION SELECT 1,2,secret_tag,4 FROM gbk_legacy_articles-- -
    """
    raw_query = request.query_string.decode('latin-1', errors='replace')
    parsed = urllib.parse.parse_qs(raw_query)
    keyword_raw = parsed.get('keyword', [''])[0]
    keyword_after_slash = _addslashes(keyword_raw)
    rows = []
    error = None
    if keyword_raw:
        try:
            if current_mode() == 'safe':
                # ✅ 统一 utf8mb4 + 参数化
                rows = run_select(
                    'SELECT article_id, keyword, title FROM gbk_legacy_articles WHERE keyword = %s',
                    (keyword_raw[:120],),
                )
            else:
                # ❌ GBK 表 + addslashes + 字符串拼接
                with get_cursor() as (_conn, cur):
                    cur.execute('SET NAMES gbk')
                    sql = (
                        'SELECT article_id, keyword, title, secret_tag FROM gbk_legacy_articles '
                        f"WHERE keyword = '{keyword_after_slash}'"
                    )
                    cur.execute(sql)
                    rows = cur.fetchall() if cur.description else []
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '关键字非法。'
    return render_lab(
        'wide_byte.html', 'wide-byte',
        rows=rows, keyword_raw=keyword_raw,
        keyword_after_slash=keyword_after_slash, error=error,
    )


# ---------- L18 WAF 黑名单绕过 ----------
# 教学用"土法 WAF"：每个关键字只替换一次（这是双写绕过能成立的前提）。
_WAF_KEYWORDS = ['union', 'select', 'from']


def _toy_waf(text_value: str) -> str:
    """模拟土法 WAF：

    1. 删空格（强制学员用 /**/ 替代）；
    2. 删常见 SQL 注释 -- / # / /* */；
    3. 对 union/select/from 各只做一次大小写无关的整词替换（双写可绕过）；
    4. 不递归替换 → 形如 ``uniunionon`` 中间的 ``union`` 被删掉一次后，
       前后 ``uni`` 与 ``on`` 拼回 ``union``，从而绕过过滤。
    """
    cleaned = text_value
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned)
    cleaned = re.sub(r'(--|#).*', '', cleaned)
    cleaned = re.sub(r'\s+', '', cleaned)
    for kw in _WAF_KEYWORDS:
        # count=1 + IGNORECASE：双写关键字时只替换一次
        cleaned = re.sub(kw, '', cleaned, count=1, flags=re.IGNORECASE)
    return cleaned


@bp.route('/labs/sqli/waf-blacklist-bypass')
def waf_blacklist_bypass():
    """教学：HPP（HTTP 参数污染）—— WAF 看第一个 q，SQL 用最后一个 q。"""
    raw_values = request.args.getlist('q')
    raw = raw_values[-1] if raw_values else ''
    waf_seen = raw_values[0] if raw_values else ''
    waf_cleaned = _toy_waf(waf_seen)
    rows = []
    error = None
    if raw:
        try:
            if current_mode() == 'safe':
                # ✅ 真正的修复：参数化 + 不再依赖黑名单
                needle = f'%{raw}%'
                rows = run_select(
                    'SELECT product_id, sku, name, price FROM products WHERE name LIKE %s LIMIT 8',
                    (needle,),
                )
            else:
                # ❌ 黑名单只清洗 waf_seen（第一个 q），实际查询用 raw（最后一个 q）
                sql = (
                    'SELECT product_id, sku, name, price FROM products '
                    f"WHERE name LIKE '%{raw}%' LIMIT 8"
                )
                rows = run_select(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '检索请求非法。'
    return render_lab(
        'waf_blacklist_bypass.html', 'waf-blacklist-bypass',
        rows=rows, raw=raw, waf_seen=waf_seen, waf_cleaned=waf_cleaned, error=error,
    )


# ---------- L19 文件读写：load_file / INTO OUTFILE ----------
@bp.route('/labs/sqli/file-rw-outfile')
def file_rw_outfile():
    """教学：UNION + LOAD_FILE() 读文件，UNION + INTO OUTFILE 写文件。

    生产环境 secure_file_priv 必须设置，且数据库账号不应有 FILE 权限。
    所有写入只能落到 /tmp/lab/（教学用沙箱目录）。
    """
    os.makedirs(LAB_FILE_OUTPUT_DIR, exist_ok=True)
    q = request.args.get('q', '')
    rows = []
    error = None
    if q:
        try:
            if current_mode() == 'safe':
                # ✅ 参数化 + 数据库账号最小权限
                rows = run_select(
                    'SELECT product_id, sku, name FROM products WHERE name LIKE %s LIMIT 5',
                    (f'%{q}%',),
                )
            else:
                # ❌ 拼接 + 高权账号，可走 LOAD_FILE / INTO OUTFILE
                sql = (
                    'SELECT product_id, sku, name FROM products '
                    f"WHERE name LIKE '%{q}%' LIMIT 5"
                )
                rows = run_select(sql)
                lowered = q.lower()
                if 'load_file' in lowered or 'outfile' in lowered:
                    op = 'read' if 'load_file' in lowered else 'write'
                    run_statement(
                        'INSERT INTO file_io_attempts (operation, target_path, result_brief) '
                        'VALUES (%s, %s, %s)',
                        (op, q[:255], '已记录至 file_io_attempts'),
                    )
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '检索非法。'
    attempts = run_select(
        'SELECT attempt_id, operation, target_path, result_brief, created_at '
        'FROM file_io_attempts ORDER BY attempt_id DESC LIMIT 10'
    )
    written_files = []
    if os.path.isdir(LAB_FILE_OUTPUT_DIR):
        for name in sorted(os.listdir(LAB_FILE_OUTPUT_DIR))[:20]:
            full = os.path.join(LAB_FILE_OUTPUT_DIR, name)
            if os.path.isfile(full):
                written_files.append({'name': name, 'size': os.path.getsize(full)})
    return render_lab(
        'file_rw_outfile.html', 'file-rw-outfile',
        rows=rows, q=q, attempts=attempts, written_files=written_files,
        sandbox_dir=LAB_FILE_OUTPUT_DIR, error=error,
    )


# ---------- L20 DNSLog 带外注入 ----------
@bp.route('/labs/sqli/oob-dnslog')
def oob_dnslog():
    """教学：演示无回显场景下的带外通道思路。

    真实利用需要 DB 主机能解析外部 DNS（容器化环境通常被禁），
    所以本关用 HTTP mock 端点 /api/sqli/dnslog/recv 模拟 DNSLog。
    """
    badge = request.args.get('badge', '')
    exists = None
    error = None
    if badge:
        try:
            if current_mode() == 'safe':
                rows = run_select(
                    'SELECT employee_id FROM employees WHERE badge_code = %s LIMIT 1',
                    (badge,),
                )
            else:
                # ❌ 拼接 + 无回显（页面只告诉 exists/not exists）
                sql = (
                    'SELECT employee_id FROM employees '
                    f"WHERE badge_code = '{badge}' LIMIT 1"
                )
                rows = run_select(sql)
            exists = bool(rows)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '查询非法。'
    callbacks = run_select(
        'SELECT callback_id, subdomain, decoded_data, received_at '
        'FROM dnslog_callbacks ORDER BY callback_id DESC LIMIT 10'
    )
    return render_lab(
        'oob_dnslog.html', 'oob-dnslog',
        badge=badge, exists=exists, callbacks=callbacks, error=error,
    )


@bp.route('/api/sqli/dnslog/recv', methods=['GET', 'POST'])
def dnslog_recv():
    """DNSLog mock 接收端：

    GET  /api/sqli/dnslog/recv?sub=<base64_or_text>
    POST /api/sqli/dnslog/recv  body: sub=<...>
    """
    sub = request.values.get('sub', '')[:160]
    decoded = ''
    if sub:
        try:
            decoded = base64.b64decode(sub + '=' * (-len(sub) % 4)).decode('utf-8', 'replace')
        except Exception:
            decoded = '(无法 base64 解码，原样保留)'
    run_statement(
        'INSERT INTO dnslog_callbacks (subdomain, decoded_data) VALUES (%s, %s)',
        (sub, decoded[:255]),
    )
    return jsonify({'ok': True, 'sub': sub, 'decoded': decoded})


# ---------- L21 NoSQL 风格注入 ----------
def _strip_quotes(value):
    """JSON_EXTRACT 返回值会带双引号，统一去掉。"""
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip('"')
    return str(value)


@bp.route('/labs/sqli/nosql-style', methods=['GET', 'POST'])
def nosql_style():
    """教学：模拟 MongoDB 的查询语义。

    vuln 模式：把 JSON body 直接当查询条件，把对象解释为操作符。
    safe 模式：强制 username/password 必须是字符串。
    """
    matched = None
    error = None
    raw_body = ''
    if request.method == 'POST':
        raw_body = request.get_data(as_text=True)
        try:
            payload = json.loads(raw_body or '{}')
            username = payload.get('username', '')
            password = payload.get('password', '')
            users = run_select(
                "SELECT JSON_EXTRACT(document_json, '$.username') AS username, "
                "       JSON_EXTRACT(document_json, '$.password') AS password, "
                "       JSON_EXTRACT(document_json, '$.role')     AS role, "
                "       JSON_EXTRACT(document_json, '$.note')     AS note "
                "FROM nosql_docs WHERE collection = 'users'"
            )
            if current_mode() == 'safe':
                # ✅ 强类型校验
                if not isinstance(username, str) or not isinstance(password, str):
                    raise ValueError('username/password 必须是字符串')
                for u in users:
                    if _strip_quotes(u['username']) == username and _strip_quotes(u['password']) == password:
                        matched = u
                        break
            else:
                # ❌ 把字段当 MongoDB 操作符：{"$ne": ""} 等价于"任何非空"
                def _match(doc_value, query_value):
                    real = _strip_quotes(doc_value)
                    if isinstance(query_value, dict):
                        if '$ne' in query_value:
                            return real != (query_value['$ne'] or '')
                        if '$gt' in query_value:
                            return real > (query_value['$gt'] or '')
                        if '$regex' in query_value:
                            return bool(re.search(query_value['$regex'], real))
                        return False
                    return real == query_value

                for u in users:
                    if _match(u['username'], username) and _match(u['password'], password):
                        matched = u
                        break
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '请求格式错误。'
    return render_lab(
        'nosql_style.html', 'nosql-style',
        matched=matched, raw_body=raw_body, error=error,
    )


# ---------- L22 方言差异速查 ----------
@bp.route('/labs/sqli/dialect-diff')
def dialect_diff():
    """教学：'看起来无害'的查询页也做成有注入。"""
    dialect = request.args.get('dialect', '')
    rows = []
    error = None
    try:
        if dialect:
            if current_mode() == 'safe':
                rows = run_select(
                    'SELECT dialect_name, feature, sample_payload, note FROM dialect_samples '
                    'WHERE dialect_name = %s',
                    (dialect,),
                )
            else:
                sql = (
                    'SELECT dialect_name, feature, sample_payload, note FROM dialect_samples '
                    f"WHERE dialect_name = '{dialect}'"
                )
                rows = run_select(sql)
        else:
            rows = run_select(
                'SELECT dialect_name, feature, sample_payload, note FROM dialect_samples'
            )
    except Exception as exc:
        error = str(exc) if current_mode() == 'vuln' else '检索非法。'
    return render_lab(
        'dialect_diff.html', 'dialect-diff',
        rows=rows, dialect=dialect, error=error,
    )


def domain_taxonomy():
    taxonomy = build_taxonomy()
    return taxonomy['position_groups'], '主轴：注入位置', '注入位置', '观察方式 / 影响'
