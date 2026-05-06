from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets

from flask import Blueprint, jsonify, redirect, render_template, request, session

from content_store import execute, query_all, query_one
from shared import current_mode
from authz_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('authz', __name__)


def get_auth_users():
    return query_all('SELECT user_id, username, display_name, role FROM auth_users ORDER BY user_id')


def get_current_user():
    user_id = session.get('auth_user_id')
    if user_id:
        user = query_one('SELECT user_id, username, display_name, role FROM auth_users WHERE user_id = ?', (user_id,))
        if user:
            return user
    first = query_one('SELECT user_id, username, display_name, role FROM auth_users ORDER BY user_id LIMIT 1')
    if first:
        session['auth_user_id'] = first['user_id']
    return first


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'authz/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, auth_users=get_auth_users(), current_auth_user=get_current_user(), **context)


def domain_info() -> dict:
    return {
        'code': 'AUTHZ',
        'title': '越权轨道',
        'description': '覆盖未授权访问、水平越权（读取/修改）与垂直越权（页面/敏感动作）。',
        'summary': '把“未认证、已认证、已授权”三层边界拆开讲清楚。',
        'level': '进阶',
        'count': len(LABS),
        'href': '/domains/authz',
        'teaching_points': [
            '先区分未授权访问与已登录后的越权。',
            '对象级授权与角色级授权分开讲。',
            '强调读和写、页面访问和敏感动作都需要独立判断。',
        ],
    }


@bp.route('/labs/authz/switch/<int:user_id>')
def switch_user(user_id: int):
    session['auth_user_id'] = user_id
    return redirect(request.args.get('next') or '/domains/authz')


@bp.route('/labs/authz/logout')
def authz_logout():
    session.pop('auth_user_id', None)
    return redirect(request.args.get('next') or '/domains/authz')


@bp.route('/labs/authz/unauth-report')
def unauth_report():
    report = None
    error = None
    if current_mode() == 'safe' and not session.get('auth_user_id'):
        error = '安全模式：未登录用户不能查看纪律报表。'
    else:
        report = query_one('SELECT * FROM auth_reports ORDER BY report_id LIMIT 1')
    return render_lab('unauth_report.html', 'unauth-report', report=report, error=error)


@bp.route('/labs/authz/horizontal-orders')
def horizontal_orders():
    user = get_current_user()
    order_id = int(request.args.get('order_id', '1001'))
    order = None
    error = None
    if current_mode() == 'safe':
        order = query_one('SELECT order_id, owner_user_id, item_name, total_amount, secret_note FROM auth_orders WHERE order_id = ? AND (owner_user_id = ? OR ? = "admin")', (order_id, user['user_id'], user['role']))
        if not order:
            error = '安全模式：当前身份无权查看该订单。'
    else:
        order = query_one('SELECT order_id, owner_user_id, item_name, total_amount, secret_note FROM auth_orders WHERE order_id = ?', (order_id,))
        if not order:
            error = '未找到该订单。'
    orders = query_all('SELECT order_id, owner_user_id, item_name, total_amount FROM auth_orders ORDER BY order_id')
    return render_lab('horizontal_orders.html', 'horizontal-orders', orders=orders, selected_order=order, error=error)


@bp.route('/labs/authz/horizontal-notes', methods=['GET', 'POST'])
def horizontal_notes():
    user = get_current_user()
    message = None
    error = None
    if request.method == 'POST':
        note_id = int(request.form.get('note_id', '0'))
        new_body = request.form.get('body', '')
        if current_mode() == 'safe':
            changed = execute('UPDATE auth_notes SET body = ?, updated_at = datetime(\'now\') WHERE note_id = ? AND (owner_user_id = ? OR ? = "admin")', (new_body, note_id, user['user_id'], user['role']))
            if not changed:
                error = '安全模式：当前身份无权修改该便签。'
            else:
                message = '便签已更新。'
        else:
            execute('UPDATE auth_notes SET body = ?, updated_at = datetime(\'now\') WHERE note_id = ?', (new_body, note_id))
            message = '便签已更新。'
    notes = query_all('SELECT note_id, owner_user_id, body, updated_at FROM auth_notes ORDER BY note_id')
    return render_lab('horizontal_notes.html', 'horizontal-notes', notes=notes, message=message, error=error)


@bp.route('/labs/authz/vertical-admin-report')
def vertical_admin_report():
    user = get_current_user()
    report_rows = query_all('SELECT username, role FROM auth_users ORDER BY user_id')
    if current_mode() == 'safe' and user['role'] != 'admin':
        return render_lab('vertical_admin_report.html', 'vertical-admin-report', report_rows=[], error='安全模式：仅管理员可访问该报表。')
    return render_lab('vertical_admin_report.html', 'vertical-admin-report', report_rows=report_rows, error=None)


@bp.route('/labs/authz/vertical-ticket-close', methods=['GET', 'POST'])
def vertical_ticket_close():
    user = get_current_user()
    message = None
    error = None
    if request.method == 'POST':
        ticket_id = int(request.form.get('ticket_id', '0'))
        if current_mode() == 'safe':
            if user['role'] != 'admin':
                error = '安全模式：只有管理员可以关闭工单。'
            else:
                execute('UPDATE auth_tickets SET status = "closed", updated_at = datetime(\'now\') WHERE ticket_id = ?', (ticket_id,))
                message = '工单已关闭。'
        else:
            execute('UPDATE auth_tickets SET status = "closed", updated_at = datetime(\'now\') WHERE ticket_id = ?', (ticket_id,))
            message = '工单已关闭。'
    tickets = query_all('SELECT ticket_id, owner_user_id, subject, status, internal_note, updated_at FROM auth_tickets ORDER BY ticket_id')
    return render_lab('vertical_ticket_close.html', 'vertical-ticket-close', tickets=tickets, message=message, error=error)


# =====================================================================
# 批次 3：Authz L05-L11 共 7 个新关卡
# =====================================================================

# JWT 演示用密钥；safe 模式会强制 HS256 + 校验签名
_JWT_SECRET = b'fieldlab-jwt-secret'

_ALLOWED_PREF_FIELDS = {'theme', 'language', 'newsletter'}
_DEBUG_ALLOWED_TABLES = {'auth_users', 'auth_orders', 'auth_invoices', 'auth_messages', 'auth_prefs'}


def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


# ---------- L05 可枚举 token ----------
@bp.route('/labs/authz/enumerable-token')
def enumerable_token():
    user = get_current_user()
    token = request.args.get('token', '')
    invoice = None
    error = None
    invoices = query_all('SELECT invoice_id, owner_user_id, amount, access_token, pdf_path FROM auth_invoices ORDER BY invoice_id')
    if token:
        if current_mode() == 'vuln':
            # ❌ 仅凭 token 即可访问，不校验 owner
            invoice = query_one('SELECT * FROM auth_invoices WHERE access_token = ?', (token,))
            if not invoice:
                error = '未找到该 token 对应的发票。'
        else:
            # ✅ 必须 token 命中且 owner 是当前用户（admin 可越级）
            invoice = query_one(
                'SELECT * FROM auth_invoices WHERE access_token = ? AND (owner_user_id = ? OR ? = "admin")',
                (token, user['user_id'], user['role']),
            )
            if not invoice:
                error = '安全模式：token 不存在或当前身份无权访问。'
    return render_lab(
        'enumerable_token.html', 'enumerable-token',
        token=token, invoice=invoice, invoices=invoices, error=error,
    )


# ---------- L06 Mass Assignment 改 owner ----------
@bp.route('/labs/authz/mass-assignment', methods=['GET', 'POST'])
def mass_assignment():
    user = get_current_user()
    message = None
    error = None
    if request.method == 'POST':
        note_id = int(request.form.get('note_id', '0'))
        body = request.form.get('body', '')
        owner_override = request.form.get('owner_user_id')
        try:
            if current_mode() == 'vuln':
                # ❌ 任意字段都拼进 UPDATE
                fields = {'body': body}
                if owner_override:
                    fields['owner_user_id'] = int(owner_override)
                set_clause = ', '.join(f'{k} = ?' for k in fields) + ', updated_at = datetime(\'now\')'
                params = list(fields.values()) + [note_id]
                execute(f'UPDATE auth_notes SET {set_clause} WHERE note_id = ?', tuple(params))
                message = f'已更新便签 #{note_id}（vuln 模式：可越权改 owner）'
            else:
                # ✅ 仅 body 字段；且必须是当前 owner 或 admin
                changed = execute(
                    'UPDATE auth_notes SET body = ?, updated_at = datetime(\'now\') '
                    'WHERE note_id = ? AND (owner_user_id = ? OR ? = "admin")',
                    (body, note_id, user['user_id'], user['role']),
                )
                if not changed:
                    raise ValueError('安全模式：当前身份无权修改该便签，且不接受 owner_user_id 字段。')
                message = f'已更新便签 #{note_id}（仅 body）'
        except Exception as exc:
            error = str(exc)
    notes = query_all('SELECT note_id, owner_user_id, body, updated_at FROM auth_notes ORDER BY note_id')
    return render_lab('mass_assignment.html', 'mass-assignment',
                      notes=notes, message=message, error=error)


# ---------- L07 偏好接口提权 ----------
@bp.route('/labs/authz/role-via-pref', methods=['GET', 'POST'])
def role_via_pref():
    user = get_current_user()
    message = None
    error = None
    if request.method == 'POST':
        try:
            payload = request.get_json(silent=True) or {}
            if not isinstance(payload, dict):
                raise ValueError('JSON body must be an object')
            if current_mode() == 'vuln':
                # ❌ merge 整段 JSON，role 也一并写入 user 表
                if 'role' in payload:
                    execute('UPDATE auth_users SET role = ? WHERE user_id = ?',
                            (payload['role'], user['user_id']))
                # 写偏好（pref 表必须先有该 user 的行）
                existing = query_one('SELECT user_id FROM auth_prefs WHERE user_id = ?', (user['user_id'],))
                if not existing:
                    execute('INSERT INTO auth_prefs (user_id, theme, language, newsletter) VALUES (?, ?, ?, ?)',
                            (user['user_id'], payload.get('theme', 'light'),
                             payload.get('language', 'zh'), int(payload.get('newsletter', 1))))
                else:
                    sets, params = [], []
                    for k in ('theme', 'language', 'newsletter'):
                        if k in payload:
                            sets.append(f'{k} = ?')
                            params.append(payload[k] if k != 'newsletter' else int(payload[k]))
                    if sets:
                        execute(f'UPDATE auth_prefs SET {", ".join(sets)} WHERE user_id = ?',
                                tuple(params + [user['user_id']]))
                message = '偏好已更新（vuln：role 也吞下了！）'
            else:
                # ✅ 字段白名单
                disallowed = [k for k in payload if k not in _ALLOWED_PREF_FIELDS]
                if disallowed:
                    raise ValueError(f'安全模式：拒绝字段 {disallowed}')
                existing = query_one('SELECT user_id FROM auth_prefs WHERE user_id = ?', (user['user_id'],))
                if not existing:
                    execute('INSERT INTO auth_prefs (user_id, theme, language, newsletter) VALUES (?, ?, ?, ?)',
                            (user['user_id'], payload.get('theme', 'light'),
                             payload.get('language', 'zh'), int(payload.get('newsletter', 1))))
                else:
                    sets, params = [], []
                    for k in ('theme', 'language', 'newsletter'):
                        if k in payload:
                            sets.append(f'{k} = ?')
                            params.append(payload[k] if k != 'newsletter' else int(payload[k]))
                    if sets:
                        execute(f'UPDATE auth_prefs SET {", ".join(sets)} WHERE user_id = ?',
                                tuple(params + [user['user_id']]))
                message = '偏好已更新（safe：role 字段被拒绝）'
        except Exception as exc:
            error = str(exc)
        return jsonify({'message': message, 'error': error,
                        'user': dict(query_one('SELECT user_id, username, role FROM auth_users WHERE user_id = ?', (user['user_id'],))),
                        'pref': dict(query_one('SELECT * FROM auth_prefs WHERE user_id = ?', (user['user_id'],)) or {})})
    pref = query_one('SELECT * FROM auth_prefs WHERE user_id = ?', (user['user_id'],))
    return render_lab('role_via_pref.html', 'role-via-pref',
                      pref=pref, message=message, error=error)


# ---------- L08 批量删除越权 ----------
@bp.route('/labs/authz/bulk-delete', methods=['GET', 'POST'])
def bulk_delete():
    user = get_current_user()
    message = None
    error = None
    if request.method == 'POST':
        ids_raw = request.form.get('note_ids', '')
        try:
            ids = [int(x) for x in ids_raw.replace(',', ' ').split() if x.strip()]
            if not ids:
                raise ValueError('至少给出一个 note_id')
            placeholders = ','.join('?' * len(ids))
            if current_mode() == 'vuln':
                # ❌ 批量接口不校验 owner
                execute(f'DELETE FROM auth_notes WHERE note_id IN ({placeholders})', tuple(ids))
                message = f'已批量删除 {len(ids)} 条（vuln：未校验 owner）'
            else:
                # ✅ 批量也要带 owner 条件
                execute(
                    f'DELETE FROM auth_notes WHERE note_id IN ({placeholders}) AND (owner_user_id = ? OR ? = "admin")',
                    tuple(ids + [user['user_id'], user['role']]),
                )
                message = f'已批量删除请求处理（仅 owner 自己的便签实际被删）'
        except Exception as exc:
            error = str(exc)
    notes = query_all('SELECT note_id, owner_user_id, body, updated_at FROM auth_notes ORDER BY note_id')
    return render_lab('bulk_delete.html', 'bulk-delete',
                      notes=notes, message=message, error=error)


# ---------- L09 私信接收人未校验 ----------
@bp.route('/labs/authz/message-receiver')
def message_receiver():
    user = get_current_user()
    msg_id = request.args.get('message_id', type=int)
    msg = None
    error = None
    if msg_id:
        if current_mode() == 'vuln':
            msg = query_one('SELECT * FROM auth_messages WHERE message_id = ?', (msg_id,))
            if not msg:
                error = '未找到该私信。'
        else:
            msg = query_one(
                'SELECT * FROM auth_messages '
                'WHERE message_id = ? AND (receiver_user_id = ? OR sender_user_id = ? OR ? = "admin")',
                (msg_id, user['user_id'], user['user_id'], user['role']),
            )
            if not msg:
                error = '安全模式：当前身份不是该私信的收发双方。'
    messages = query_all('SELECT message_id, sender_user_id, receiver_user_id, subject FROM auth_messages ORDER BY message_id')
    return render_lab('message_receiver.html', 'message-receiver',
                      message_id=msg_id, message=msg, messages=messages, error=error)


# ---------- L10 JWT alg=none ----------
def _jwt_decode_safe(token: str) -> dict:
    """safe：强制 HS256 + 校验签名。"""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('token 不是三段式')
    header = json.loads(_b64url_decode(parts[0]))
    if header.get('alg') != 'HS256':
        raise ValueError(f'安全模式：仅支持 alg=HS256，收到 {header.get("alg")}')
    signing_input = f'{parts[0]}.{parts[1]}'.encode()
    expected = hmac.new(_JWT_SECRET, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(parts[2]), expected):
        raise ValueError('签名不匹配')
    return json.loads(_b64url_decode(parts[1]))


def _jwt_decode_vuln(token: str) -> dict:
    """vuln：尊重 header.alg；alg=none 时不校验签名。"""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('token 不是三段式')
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    if header.get('alg') == 'none':
        return payload  # ❌ 不校验签名
    if header.get('alg') == 'HS256':
        signing_input = f'{parts[0]}.{parts[1]}'.encode()
        expected = hmac.new(_JWT_SECRET, signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_decode(parts[2]), expected):
            raise ValueError('签名不匹配')
        return payload
    raise ValueError(f'未知 alg={header.get("alg")}')


@bp.route('/labs/authz/jwt-none-alg', methods=['GET', 'POST'])
def jwt_none_alg():
    user = get_current_user()
    # 提供合法 token 给学员当起点
    legit_header = _b64url_encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}, separators=(',', ':')).encode())
    legit_payload = _b64url_encode(json.dumps({'sub': user['username'], 'role': user['role']}, separators=(',', ':')).encode())
    legit_sig = _b64url_encode(hmac.new(_JWT_SECRET, f'{legit_header}.{legit_payload}'.encode(), hashlib.sha256).digest())
    legit_token = f'{legit_header}.{legit_payload}.{legit_sig}'

    submitted = request.values.get('token', '')
    decoded = None
    is_admin = False
    error = None
    if submitted:
        try:
            decoded = (_jwt_decode_vuln if current_mode() == 'vuln' else _jwt_decode_safe)(submitted)
            is_admin = decoded.get('role') == 'admin'
        except Exception as exc:
            error = str(exc)
    return render_lab('jwt_none_alg.html', 'jwt-none-alg',
                      legit_token=legit_token, submitted=submitted,
                      decoded=decoded, is_admin=is_admin, error=error)


# ---------- L11 调试接口暴露 ----------
@bp.route('/labs/authz/debug-endpoint')
def debug_endpoint():
    table = request.args.get('table', '')
    rows = None
    error = None
    if table:
        if table not in _DEBUG_ALLOWED_TABLES:
            error = f'未知表：{table}'
        elif current_mode() == 'safe':
            if request.headers.get('X-Debug-Token') != 'lab-debug-token':
                error = '安全模式：缺少 X-Debug-Token 头，调试接口已禁用。'
            else:
                rows = query_all(f'SELECT * FROM {table} LIMIT 50')
        else:
            # ❌ vuln：完全不鉴权
            rows = query_all(f'SELECT * FROM {table} LIMIT 50')
    return render_lab('debug_endpoint.html', 'debug-endpoint',
                      table=table, rows=rows, error=error,
                      allowed_tables=sorted(_DEBUG_ALLOWED_TABLES))


def domain_taxonomy():
    return build_taxonomy(), '主轴：授权缺陷类型', '授权缺陷类型', '缺失的校验点'
