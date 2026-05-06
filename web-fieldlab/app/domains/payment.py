from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from decimal import Decimal, getcontext
from uuid import uuid4

from flask import Blueprint, jsonify, render_template, request

from content_store import execute, query_all, query_one
from payment_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

getcontext().prec = 28

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
            message = f'下单完成：原价 {product["price"]:.2f}，券后 {final_amount:.2f}'
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


# =====================================================================
# 批次 4：payment L05-L10 共 6 个新关卡
# =====================================================================

_CALLBACK_SECRET = b'fieldlab-callback-secret'
_VALID_STATE_TRANSITIONS = {
    'pending': {'paid', 'cancelled'},
    'paid': {'refunded', 'partial_refund'},
    'partial_refund': {'refunded'},
    'refunded': set(),
    'cancelled': set(),
}


def _sign_callback(order_ref: str, amount: float, nonce: str = '') -> str:
    msg = f'{order_ref}|{amount}|{nonce}'.encode()
    return hmac.new(_CALLBACK_SECRET, msg, hashlib.sha256).hexdigest()[:16]


# ---------- L05 浮点累加 ----------
@bp.route('/labs/payment/float-precision', methods=['GET', 'POST'])
def float_precision():
    """vuln：用 float 累加；safe：用 Decimal。
    通过提交 N 与 unit 来批量充值，比对 expected (N * unit) 与累加结果。"""
    message = None
    error = None
    if request.method == 'POST':
        try:
            count = int(request.form.get('count', '1000'))
            unit = request.form.get('unit', '0.1')
            if count <= 0 or count > 100000:
                raise ValueError('count 必须在 1..100000 之间')
            if current_mode() == 'vuln':
                actual = 0.0
                u = float(unit)
                for _ in range(count):
                    actual += u
                expected_str = f'{count * float(unit):.10f}'
                actual_str = f'{actual:.10f}'
                drift = float(unit) * count - actual
            else:
                d_unit = Decimal(unit)
                actual_dec = Decimal('0')
                for _ in range(count):
                    actual_dec += d_unit
                expected_dec = d_unit * count
                expected_str = str(expected_dec)
                actual_str = str(actual_dec)
                drift = float(expected_dec - actual_dec)
            message = (f'count={count}, unit={unit}\n'
                       f'expected = {expected_str}\n'
                       f'actual   = {actual_str}\n'
                       f'drift    = {drift!r}')
        except Exception as exc:
            error = str(exc)
    return render_lab('float_precision.html', 'float-precision',
                      message=message, error=error)


# ---------- L06 货币单位混淆 ----------
@bp.route('/labs/payment/currency-unit', methods=['GET', 'POST'])
def currency_unit():
    """vuln：服务端把客户端 amount 当"元"入账，不校验单位。
    safe：服务端只接收 amount_cents（int），并校验 == price_cents。"""
    message = None
    error = None
    products = query_all('SELECT * FROM payment_products ORDER BY product_id')
    if request.method == 'POST':
        try:
            product = query_one('SELECT * FROM payment_products WHERE product_id = ?',
                                (int(request.form.get('product_id', '1')),))
            if not product:
                raise ValueError('product 不存在')
            if current_mode() == 'vuln':
                # ❌ 客户端 amount 直接当元
                client_amount = float(request.form.get('amount', '0'))
                accepted = client_amount
                note = f'client amount={client_amount}（vuln 当元入账，期望 ¥{product["price"]}）'
            else:
                # ✅ 只接 amount_cents int，并校验
                try:
                    cents = int(request.form.get('amount_cents', '0'))
                except ValueError:
                    raise ValueError('safe：amount_cents 必须是整数')
                price_cents = int(round(product['price'] * 100))
                if cents != price_cents:
                    raise ValueError(f'safe：amount_cents 必须等于 {price_cents}（¥{product["price"]}）')
                accepted = cents / 100.0
                note = f'amount_cents={cents}（safe 校验单位）'
            order_ref = 'CURR-' + uuid4().hex[:8].upper()
            execute('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime(\'now\'))',
                    (order_ref, 'alice', product['name'], product['price'], accepted, 'paid', note))
            message = f'订单 {order_ref}：expected={product["price"]} / accepted={accepted}'
        except Exception as exc:
            error = str(exc)
    orders = query_all("SELECT order_ref, product_name, expected_amount, paid_amount, note, created_at FROM payment_orders WHERE order_ref LIKE 'CURR-%' ORDER BY order_id DESC LIMIT 8")
    return render_lab('currency_unit.html', 'currency-unit',
                      products=products, orders=orders, message=message, error=error)


# ---------- L07 退款超额 ----------
@bp.route('/labs/payment/refund-overpay', methods=['GET', 'POST'])
def refund_overpay():
    message = None
    error = None
    if request.method == 'POST':
        try:
            order_ref = request.form.get('order_ref', '').strip()
            refund_amount = float(request.form.get('refund_amount', '0'))
            order = query_one('SELECT * FROM payment_orders WHERE order_ref = ?', (order_ref,))
            if not order:
                raise ValueError('订单不存在')
            if refund_amount <= 0:
                raise ValueError('退款金额必须为正')
            already_refunded = query_one(
                'SELECT COALESCE(SUM(refund_amount), 0) AS s FROM payment_refunds WHERE order_ref = ?',
                (order_ref,),
            )['s'] or 0.0
            if current_mode() == 'safe':
                # ✅ 校验退款不超 paid - 已退
                allowed = order['paid_amount'] - already_refunded
                if refund_amount > allowed + 1e-9:
                    raise ValueError(f'safe：超出可退额度 {allowed:.2f}')
            # vuln：直接执行
            execute(
                'INSERT INTO payment_refunds (order_ref, refund_amount, mode, created_at) VALUES (?, ?, ?, datetime(\'now\'))',
                (order_ref, refund_amount, current_mode()),
            )
            execute(
                'UPDATE payment_wallets SET balance = balance + ? WHERE owner_label = ?',
                (refund_amount, order['owner_label']),
            )
            message = (f'退款 {refund_amount:.2f} 已记入。订单 paid={order["paid_amount"]}, '
                       f'已退累计={already_refunded + refund_amount:.2f}')
        except Exception as exc:
            error = str(exc)
    orders = query_all('SELECT order_ref, product_name, paid_amount, status, created_at FROM payment_orders WHERE status IN ("paid","partial_refund","refunded") ORDER BY order_id DESC LIMIT 8')
    refunds = query_all('SELECT * FROM payment_refunds ORDER BY refund_id DESC LIMIT 12')
    wallet = _wallet()
    return render_lab('refund_overpay.html', 'refund-overpay',
                      orders=orders, refunds=refunds, wallet=wallet,
                      message=message, error=error)


# ---------- L08 状态机 ----------
@bp.route('/labs/payment/state-machine', methods=['GET', 'POST'])
def state_machine():
    message = None
    error = None
    if request.method == 'POST':
        try:
            order_ref = request.form.get('order_ref', '').strip()
            target_status = request.form.get('target_status', '').strip()
            order = query_one('SELECT * FROM payment_orders WHERE order_ref = ?', (order_ref,))
            if not order:
                raise ValueError('订单不存在')
            if current_mode() == 'safe':
                allowed = _VALID_STATE_TRANSITIONS.get(order['status'], set())
                if target_status not in allowed:
                    raise ValueError(f'safe：拒绝 {order["status"]} -> {target_status}（allowed={sorted(allowed)}）')
            execute('UPDATE payment_orders SET status = ? WHERE order_ref = ?', (target_status, order_ref))
            message = f'{order_ref}: {order["status"]} -> {target_status}'
        except Exception as exc:
            error = str(exc)
    orders = query_all('SELECT order_ref, product_name, paid_amount, status, created_at FROM payment_orders ORDER BY order_id DESC LIMIT 8')
    return render_lab('state_machine.html', 'state-machine',
                      orders=orders, transitions=_VALID_STATE_TRANSITIONS,
                      message=message, error=error)


# ---------- L09 签名重放 ----------
@bp.route('/labs/payment/signature-replay', methods=['GET', 'POST'])
def signature_replay():
    message = None
    error = None
    sample = None
    # 提供合法签名给学员当起点
    sample_order = query_one('SELECT * FROM payment_orders WHERE order_ref = ?', ('PAY-30003',))
    if sample_order:
        sample = {
            'order_ref': sample_order['order_ref'],
            'amount': sample_order['expected_amount'],
            'nonce': secrets.token_hex(8),
        }
        sample['signature'] = _sign_callback(sample['order_ref'], sample['amount'], sample['nonce'])
    if request.method == 'POST':
        try:
            order_ref = request.form.get('order_ref', '').strip()
            amount = float(request.form.get('amount', '0'))
            nonce = request.form.get('nonce', '').strip()
            sig = request.form.get('signature', '').strip()
            order = query_one('SELECT * FROM payment_orders WHERE order_ref = ?', (order_ref,))
            if not order:
                raise ValueError('订单不存在')
            if current_mode() == 'vuln':
                # ❌ 签名只覆盖 order_ref + amount，nonce 字段服务端忽略
                expected_sig = _sign_callback(order_ref, amount, '')
                if not hmac.compare_digest(sig, expected_sig):
                    raise ValueError('vuln：签名无效')
                # 不去重，每次都加点券
            else:
                # ✅ 签名必须包含 nonce + 服务端去重
                expected_sig = _sign_callback(order_ref, amount, nonce)
                if not hmac.compare_digest(sig, expected_sig):
                    raise ValueError('safe：签名无效（必须含 nonce）')
                if not nonce:
                    raise ValueError('safe：缺少 nonce')
                used = query_one('SELECT 1 FROM payment_callback_nonces WHERE nonce = ?', (nonce,))
                if used:
                    raise ValueError('safe：nonce 已使用')
                execute('INSERT INTO payment_callback_nonces (nonce, order_ref, used_at) VALUES (?, ?, datetime(\'now\'))',
                        (nonce, order_ref))
            execute('UPDATE payment_orders SET callback_count = callback_count + 1 WHERE order_ref = ?', (order_ref,))
            execute('UPDATE payment_wallets SET credits = credits + 100 WHERE owner_label = ?', ('alice',))
            message = '回调已记账，credits +100。'
        except Exception as exc:
            error = str(exc)
    wallet = _wallet()
    orders = query_all('SELECT order_ref, callback_count, status FROM payment_orders ORDER BY order_id DESC LIMIT 8')
    nonces = query_all('SELECT nonce, order_ref, used_at FROM payment_callback_nonces ORDER BY used_at DESC LIMIT 8')
    return render_lab('signature_replay.html', 'signature-replay',
                      sample=sample, wallet=wallet, orders=orders, nonces=nonces,
                      message=message, error=error)


# ---------- L10 限量秒杀超卖 ----------
_FLASH_LOCK = threading.Lock()  # 仅在 safe 模式额外用作"应用层锁"


def _grab_flash_vuln(code: str, owner: str) -> tuple[bool, str]:
    """vuln：先 SELECT 再 UPDATE，并主动 sleep 制造窗口。"""
    coupon = query_one('SELECT remaining FROM payment_flash_coupons WHERE code = ?', (code,))
    if not coupon:
        return False, '券不存在'
    if coupon['remaining'] <= 0:
        return False, '已抢光'
    # ❌ 故意放大 TOCTOU 窗口，让并发能稳定复现超卖
    time.sleep(0.05)
    execute('UPDATE payment_flash_coupons SET remaining = remaining - 1 WHERE code = ?', (code,))
    execute('INSERT INTO payment_flash_grants (code, owner_label, mode, created_at) VALUES (?, ?, "vuln", datetime(\'now\'))',
            (code, owner))
    return True, 'granted'


def _grab_flash_safe(code: str, owner: str) -> tuple[bool, str]:
    """safe：UPDATE WHERE remaining > 0 + 检查 rowcount。"""
    changed = execute(
        'UPDATE payment_flash_coupons SET remaining = remaining - 1 WHERE code = ? AND remaining > 0',
        (code,),
    )
    if not changed:
        return False, '已抢光'
    execute('INSERT INTO payment_flash_grants (code, owner_label, mode, created_at) VALUES (?, ?, "safe", datetime(\'now\'))',
            (code, owner))
    return True, 'granted'


@bp.route('/labs/payment/oversell-flash', methods=['GET', 'POST'])
def oversell_flash():
    message = None
    error = None
    code = 'FLASH-5'
    if request.method == 'POST':
        action = request.form.get('action', '')
        try:
            if action == 'reset':
                execute('UPDATE payment_flash_coupons SET remaining = total WHERE code = ?', (code,))
                execute('DELETE FROM payment_flash_grants WHERE code = ?', (code,))
                message = '已重置 FLASH-5 库存与领取记录。'
            elif action == 'concurrent_grab':
                threads = int(request.form.get('threads', '20'))
                threads = max(1, min(threads, 50))
                results = {'ok': 0, 'reject': 0}
                lock = threading.Lock()
                grab_fn = _grab_flash_vuln if current_mode() == 'vuln' else _grab_flash_safe

                def worker(idx: int):
                    ok, _ = grab_fn(code, f'attacker-{idx:02d}')
                    with lock:
                        results['ok' if ok else 'reject'] += 1

                ts = []
                for i in range(threads):
                    t = threading.Thread(target=worker, args=(i,))
                    ts.append(t)
                    t.start()
                for t in ts:
                    t.join(timeout=10)
                remaining = query_one('SELECT remaining, total FROM payment_flash_coupons WHERE code = ?', (code,))
                message = (f'并发 {threads} 次：success={results["ok"]} reject={results["reject"]}；'
                           f'剩余 {remaining["remaining"]}/{remaining["total"]}')
            elif action == 'single_grab':
                grab_fn = _grab_flash_vuln if current_mode() == 'vuln' else _grab_flash_safe
                ok, msg = grab_fn(code, request.form.get('owner', 'alice'))
                message = f'single grab: ok={ok}, msg={msg}'
            else:
                raise ValueError(f'未知 action: {action}')
        except Exception as exc:
            error = str(exc)
    coupon = query_one('SELECT * FROM payment_flash_coupons WHERE code = ?', (code,))
    grants = query_all('SELECT * FROM payment_flash_grants WHERE code = ? ORDER BY grant_id DESC LIMIT 30', (code,))
    return render_lab('oversell_flash.html', 'oversell-flash',
                      coupon=coupon, grants=grants, message=message, error=error)


def domain_taxonomy():
    return build_taxonomy(), '主轴：支付逻辑风险面', '支付逻辑风险面', '出错的规则'
