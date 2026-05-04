from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, render_template, request

from content_store import execute, query_all, query_one
from race_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

bp = Blueprint('race', __name__)
LOCKS = {
    'coupon': threading.Lock(),
    'inventory': threading.Lock(),
    'wallet': threading.Lock(),
    'seat': threading.Lock(),
}


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'race/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, **context)


def domain_info() -> dict:
    return {
        'code': 'RACE',
        'title': '条件竞争轨道',
        'description': '通过并发模拟按钮讲清 check-then-update、超卖、双花和席位抢占。',
        'summary': '每关都能一键并发复现，再切安全模式看锁/原子更新差异。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/race',
        'teaching_points': [
            '先讲共享状态，再讲并发窗口。',
            '不要把 race condition 当成“偶现 bug”，而要当成授权/记账级安全问题。',
            '课堂里直接并发复现，比口头解释更有效。',
        ],
    }


def _log(lab_slug: str, attempts: int, success_count: int, detail: str):
    execute('INSERT INTO race_logs (lab_slug, attempts, success_count, detail, created_at) VALUES (?, ?, ?, ?, datetime(\'now\'))', (lab_slug, attempts, success_count, detail))


def _run_burst(fn, attempts: int):
    with ThreadPoolExecutor(max_workers=attempts) as pool:
        results = list(pool.map(lambda _i: fn(), range(attempts)))
    success = sum(1 for item in results if item)
    return success, results


def _coupon_once():
    row = query_one('SELECT remaining_uses FROM race_coupons WHERE code = ?', ('RACE-ONCE',))
    if not row or row['remaining_uses'] <= 0:
        return False
    time.sleep(0.05)
    execute('UPDATE race_coupons SET remaining_uses = ? WHERE code = ?', (row['remaining_uses'] - 1, 'RACE-ONCE'))
    return True


def _inventory_once():
    row = query_one('SELECT stock FROM race_inventory WHERE sku = ?', ('hoodie-one',))
    if not row or row['stock'] <= 0:
        return False
    time.sleep(0.05)
    execute('UPDATE race_inventory SET stock = ? WHERE sku = ?', (row['stock'] - 1, 'hoodie-one'))
    return True


def _wallet_once():
    row = query_one('SELECT balance FROM race_wallets WHERE owner = ?', ('alice',))
    if not row or row['balance'] < 20:
        return False
    time.sleep(0.05)
    execute('UPDATE race_wallets SET balance = ? WHERE owner = ?', (row['balance'] - 20, 'alice'))
    return True


def _seat_once():
    row = query_one('SELECT remaining FROM race_seats WHERE event_name = ?', ('masterclass-seat',))
    if not row or row['remaining'] <= 0:
        return False
    time.sleep(0.05)
    execute('UPDATE race_seats SET remaining = ? WHERE event_name = ?', (row['remaining'] - 1, 'masterclass-seat'))
    return True


def _run_with_lock(lock_name: str, fn):
    def inner():
        with LOCKS[lock_name]:
            return fn()
    return inner


@bp.route('/labs/race/coupon-burst', methods=['GET', 'POST'])
def coupon_burst():
    message = None
    if request.method == 'POST':
        attempts = int(request.form.get('attempts', '8'))
        fn = _coupon_once if current_mode() == 'vuln' else _run_with_lock('coupon', _coupon_once)
        success, _ = _run_burst(fn, attempts)
        remaining = query_one('SELECT remaining_uses FROM race_coupons WHERE code = ?', ('RACE-ONCE',))['remaining_uses']
        detail = f'remaining={remaining}'
        _log('coupon-burst', attempts, success, detail)
        message = f'并发 {attempts} 次，成功 {success} 次，剩余={remaining}'
    state = query_one('SELECT * FROM race_coupons WHERE code = ?', ('RACE-ONCE',))
    logs = query_all("SELECT * FROM race_logs WHERE lab_slug = 'coupon-burst' ORDER BY log_id DESC LIMIT 8")
    return render_lab('coupon_burst.html', 'coupon-burst', state=state, logs=logs, message=message)


@bp.route('/labs/race/inventory-burst', methods=['GET', 'POST'])
def inventory_burst():
    message = None
    if request.method == 'POST':
        attempts = int(request.form.get('attempts', '8'))
        fn = _inventory_once if current_mode() == 'vuln' else _run_with_lock('inventory', _inventory_once)
        success, _ = _run_burst(fn, attempts)
        stock = query_one('SELECT stock FROM race_inventory WHERE sku = ?', ('hoodie-one',))['stock']
        _log('inventory-burst', attempts, success, f'stock={stock}')
        message = f'并发 {attempts} 次，成功 {success} 次，stock={stock}'
    state = query_one('SELECT * FROM race_inventory WHERE sku = ?', ('hoodie-one',))
    logs = query_all("SELECT * FROM race_logs WHERE lab_slug = 'inventory-burst' ORDER BY log_id DESC LIMIT 8")
    return render_lab('inventory_burst.html', 'inventory-burst', state=state, logs=logs, message=message)


@bp.route('/labs/race/wallet-burst', methods=['GET', 'POST'])
def wallet_burst():
    message = None
    if request.method == 'POST':
        attempts = int(request.form.get('attempts', '4'))
        fn = _wallet_once if current_mode() == 'vuln' else _run_with_lock('wallet', _wallet_once)
        success, _ = _run_burst(fn, attempts)
        balance = query_one('SELECT balance FROM race_wallets WHERE owner = ?', ('alice',))['balance']
        _log('wallet-burst', attempts, success, f'balance={balance}')
        message = f'并发 {attempts} 次，成功 {success} 次，balance={balance}'
    state = query_one('SELECT * FROM race_wallets WHERE owner = ?', ('alice',))
    logs = query_all("SELECT * FROM race_logs WHERE lab_slug = 'wallet-burst' ORDER BY log_id DESC LIMIT 8")
    return render_lab('wallet_burst.html', 'wallet-burst', state=state, logs=logs, message=message)


@bp.route('/labs/race/seat-burst', methods=['GET', 'POST'])
def seat_burst():
    message = None
    if request.method == 'POST':
        attempts = int(request.form.get('attempts', '6'))
        fn = _seat_once if current_mode() == 'vuln' else _run_with_lock('seat', _seat_once)
        success, _ = _run_burst(fn, attempts)
        remaining = query_one('SELECT remaining FROM race_seats WHERE event_name = ?', ('masterclass-seat',))['remaining']
        _log('seat-burst', attempts, success, f'remaining={remaining}')
        message = f'并发 {attempts} 次，成功 {success} 次，remaining={remaining}'
    state = query_one('SELECT * FROM race_seats WHERE event_name = ?', ('masterclass-seat',))
    logs = query_all("SELECT * FROM race_logs WHERE lab_slug = 'seat-burst' ORDER BY log_id DESC LIMIT 8")
    return render_lab('seat_burst.html', 'seat-burst', state=state, logs=logs, message=message)


def domain_taxonomy():
    return build_taxonomy(), '主轴：共享状态类型', '共享状态类型', '窗口类型'
