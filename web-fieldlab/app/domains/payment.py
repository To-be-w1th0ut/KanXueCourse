from __future__ import annotations

from uuid import uuid4

from flask import Blueprint, render_template, request

from content_store import execute, query_all, query_one
from payment_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

bp = Blueprint('payment', __name__)


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'payment/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, **context)


def domain_info() -> dict:
    return {
        'code': 'PAY',
        'title': '支付逻辑轨道',
        'description': '围绕客户端价格信任、符号边界、优惠券消耗与回调幂等。',
        'summary': '突出“没有注入也能出大事”的业务逻辑漏洞。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/payment',
        'teaching_points': [
            '先讲“服务端重算价格”这一核心原则。',
            '再讲状态消费：优惠券、库存、余额、回调都属于状态机。',
            '最后强调幂等、原子性和服务端规则。',
        ],
    }


def _wallet():
    return query_one('SELECT owner_label, balance, credits FROM payment_wallets WHERE owner_label = ?', ('alice',))


@bp.route('/labs/payment/client-total', methods=['GET', 'POST'])
def client_total():
    message = None
    error = None
    if request.method == 'POST':
        product = query_one('SELECT * FROM payment_products WHERE product_id = ?', (int(request.form.get('product_id', '1')),))
        client_total = float(request.form.get('client_total', '0'))
        qty = int(request.form.get('quantity', '1'))
        expected = product['price'] * qty
        accepted = client_total if current_mode() == 'vuln' else expected
        order_ref = 'PAY-' + uuid4().hex[:8].upper()
        execute('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime(\'now\'))', (order_ref, 'alice', product['name'], expected, accepted, 'paid', f'client_total={client_total} quantity={qty}'))
        message = f'订单已创建：expected={expected:.2f} / accepted={accepted:.2f}'
    products = query_all('SELECT * FROM payment_products ORDER BY product_id')
    orders = query_all('SELECT order_ref, product_name, expected_amount, paid_amount, status, note, created_at FROM payment_orders ORDER BY order_id DESC LIMIT 8')
    return render_lab('client_total.html', 'client-total', products=products, orders=orders, message=message, error=error)


@bp.route('/labs/payment/negative-quantity', methods=['GET', 'POST'])
def negative_quantity():
    message = None
    error = None
    wallet = _wallet()
    product = query_one('SELECT * FROM payment_products WHERE product_id = 2')
    if request.method == 'POST':
        qty = int(request.form.get('quantity', '1'))
        try:
            if current_mode() == 'safe' and qty <= 0:
                raise ValueError('安全模式要求 quantity 必须是正整数。')
            delta = qty * product['price']
            new_balance = wallet['balance'] - delta
            if current_mode() == 'safe' and new_balance < 0:
                raise ValueError('安全模式：余额不足。')
            execute('UPDATE payment_wallets SET balance = ? WHERE owner_label = ?', (new_balance, wallet['owner_label']))
            message = f'处理完成：quantity={qty}, delta={delta:.2f}, balance -> {new_balance:.2f}'
        except Exception as exc:
            error = str(exc)
    wallet = _wallet()
    return render_lab('negative_quantity.html', 'negative-quantity', wallet=wallet, product=product, message=message, error=error)


@bp.route('/labs/payment/coupon-reuse', methods=['GET', 'POST'])
def coupon_reuse():
    message = None
    error = None
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        product = query_one('SELECT * FROM payment_products WHERE product_id = 1')
        coupon = query_one('SELECT * FROM payment_coupons WHERE code = ?', (code,))
        try:
            if not coupon or not coupon['active'] or coupon['remaining_uses'] <= 0:
                raise ValueError('优惠券不可用。')
            final_amount = max(product['price'] - coupon['discount_amount'], 0)
            if current_mode() == 'safe':
                changed = execute('UPDATE payment_coupons SET remaining_uses = remaining_uses - 1 WHERE code = ? AND remaining_uses > 0', (code,))
                if not changed:
                    raise ValueError('安全模式：优惠券已被消耗。')
            order_ref = 'COUPON-' + uuid4().hex[:8].upper()
            execute('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime(\'now\'))', (order_ref, 'alice', product['name'], product['price'], final_amount, 'paid', f'coupon={code}'))
            message = f'下单完成：原价 {product['price']:.2f}，券后 {final_amount:.2f}'
        except Exception as exc:
            error = str(exc)
    coupons = query_all('SELECT * FROM payment_coupons ORDER BY code')
    orders = query_all("SELECT order_ref, note, expected_amount, paid_amount, created_at FROM payment_orders WHERE note LIKE 'coupon=%' ORDER BY order_id DESC LIMIT 8")
    return render_lab('coupon_reuse.html', 'coupon-reuse', coupons=coupons, orders=orders, message=message, error=error)


@bp.route('/labs/payment/duplicate-callback', methods=['GET', 'POST'])
def duplicate_callback():
    message = None
    error = None
    if request.method == 'POST':
        order_ref = request.form.get('order_ref', '')
        order = query_one('SELECT * FROM payment_orders WHERE order_ref = ?', (order_ref,))
        wallet = _wallet()
        try:
            if not order:
                raise ValueError('订单不存在。')
            if current_mode() == 'safe' and order['status'] == 'settled':
                raise ValueError('安全模式：该回调已经处理过。')
            execute('UPDATE payment_orders SET callback_count = callback_count + 1, paid_amount = paid_amount + expected_amount, status = ? WHERE order_ref = ?', ('settled', order_ref))
            execute('UPDATE payment_wallets SET credits = credits + 100 WHERE owner_label = ?', (wallet['owner_label'],))
            message = '回调已处理：订单加记一次支付、账户增加 100 点券。'
        except Exception as exc:
            error = str(exc)
    wallet = _wallet()
    orders = query_all('SELECT order_ref, product_name, expected_amount, paid_amount, status, callback_count, created_at FROM payment_orders ORDER BY order_id DESC LIMIT 8')
    return render_lab('duplicate_callback.html', 'duplicate-callback', wallet=wallet, orders=orders, message=message, error=error)


def domain_taxonomy():
    return build_taxonomy(), '主轴：支付逻辑风险面', '支付逻辑风险面', '出错的规则'
