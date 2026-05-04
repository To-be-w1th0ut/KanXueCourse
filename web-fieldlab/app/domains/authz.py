from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session

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


def domain_taxonomy():
    return build_taxonomy(), '主轴：授权缺陷类型', '授权缺陷类型', '缺失的校验点'
