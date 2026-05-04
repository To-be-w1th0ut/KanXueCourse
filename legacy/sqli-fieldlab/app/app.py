from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation

from flask import Flask, jsonify, render_template, request
from sqlalchemy import text

from config import Config
from db import engine, run_multi_statement, run_select, run_statement
from labs import LABS, build_taxonomy, get_lab

app = Flask(__name__)
app.config.from_object(Config)


@app.context_processor
def inject_globals():
    return {"all_labs": LABS, "app_public_port": Config.APP_PUBLIC_PORT}


def current_mode() -> str:
    return "safe" if request.args.get("mode") == "safe" else "vuln"


def render_lab(template_name: str, slug: str, **context):
    return render_template(template_name, lab=get_lab(slug), mode=current_mode(), **context)


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
        ok = run_select("SELECT 1 AS ok")
        return jsonify({"status": "ok", "db": ok[0]["ok"]})
    except Exception as exc:  # pragma: no cover - operational endpoint
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/labs/login-bypass", methods=["GET", "POST"])
def login_bypass():
    matched_user = None
    result = None
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            if current_mode() == "safe":
                rows = run_select(
                    "SELECT username, role, display_name, department FROM users WHERE username = %s AND password = %s LIMIT 1",
                    (username, password),
                )
            else:
                sql = (
                    "SELECT username, role, display_name, department FROM users "
                    f"WHERE username = '{username}' AND password = '{password}' LIMIT 1"
                )
                rows = run_select(sql)
            if rows:
                matched_user = rows[0]
                result = "登录成功"
            else:
                result = "登录失败"
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "请求处理失败。"
    return render_lab("labs/login_bypass.html", "login-bypass", matched_user=matched_user, result=result, error=error)


@app.route("/labs/product-union")
def product_union():
    q = request.args.get("q", "")
    rows = []
    error = None
    if q:
        try:
            if current_mode() == "safe":
                needle = f"%{q}%"
                rows = run_select(
                    "SELECT product_id, sku, name, price, category FROM products WHERE name LIKE %s OR description LIKE %s LIMIT 8",
                    (needle, needle),
                )
            else:
                sql = (
                    "SELECT product_id, sku, name, price, category FROM products "
                    f"WHERE name LIKE '%{q}%' OR description LIKE '%{q}%' LIMIT 8"
                )
                rows = run_select(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "搜索请求无效。"
    return render_lab("labs/product_union.html", "product-union", rows=rows, q=q, error=error)


@app.route("/labs/error-ticket")
def error_ticket():
    ticket_id = request.args.get("id", "1")
    rows = []
    error = None
    if ticket_id:
        try:
            if current_mode() == "safe":
                rows = run_select(
                    "SELECT ticket_id, title, status, owner_email, severity FROM support_tickets WHERE ticket_id = %s",
                    (int(ticket_id),),
                )
            else:
                sql = (
                    "SELECT ticket_id, title, status, owner_email, internal_note, severity "
                    f"FROM support_tickets WHERE ticket_id = {ticket_id}"
                )
                rows = run_select(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "参数非法，详细错误已隐藏。"
    return render_lab("labs/error_ticket.html", "error-ticket", ticket_id=ticket_id, rows=rows, error=error)


@app.route("/labs/employee-blind")
def employee_blind():
    badge = request.args.get("badge", "")
    exists = None
    if badge:
        if current_mode() == "safe":
            rows = run_select(
                "SELECT employee_id FROM employees WHERE badge_code = %s AND active = 1 LIMIT 1",
                (badge,),
            )
        else:
            sql = (
                "SELECT employee_id FROM employees "
                f"WHERE badge_code = '{badge}' AND active = 1 LIMIT 1"
            )
            rows = run_select(sql)
        exists = bool(rows)
    return render_lab("labs/employee_blind.html", "employee-blind", badge=badge, exists=exists)


@app.route("/labs/shipping-time")
def shipping_time():
    order_number = request.args.get("order", "")
    status = None
    elapsed = None
    error = None
    if order_number:
        start = time.perf_counter()
        try:
            if current_mode() == "safe":
                rows = run_select(
                    "SELECT status FROM orders WHERE order_number = %s LIMIT 1",
                    (order_number,),
                )
            else:
                sql = f"SELECT status FROM orders WHERE order_number = '{order_number}' LIMIT 1"
                rows = run_select(sql)
            status = rows[0]["status"] if rows else "未找到对应订单或结果被抑制"
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "请求被拒绝。"
        finally:
            elapsed = round(time.perf_counter() - start, 3)
    return render_lab(
        "labs/shipping_time.html",
        "shipping-time",
        order_number=order_number,
        status=status,
        elapsed=elapsed,
        error=error,
    )


@app.route("/labs/report-stacked")
def report_stacked():
    month = request.args.get("month", "2026-04")
    rows = []
    message = None
    error = None
    try:
        if current_mode() == "safe":
            rows = run_select(
                "SELECT log_id, actor, action, source_ip, created_at FROM audit_logs WHERE action_month = %s ORDER BY created_at DESC LIMIT 15",
                (month,),
            )
        else:
            sql = (
                "SELECT log_id, actor, action, source_ip, created_at FROM audit_logs "
                f"WHERE action_month = '{month}' ORDER BY created_at DESC LIMIT 15;"
            )
            result_sets = run_multi_statement(sql)
            first = result_sets[0] if result_sets else []
            rows = first if isinstance(first, list) else []
            if len(result_sets) > 1:
                message = f"本次请求额外执行了 {len(result_sets) - 1} 条后续语句。"
    except Exception as exc:
        error = str(exc) if current_mode() == "vuln" else "参数不符合报表规范。"
    sample_grades = run_select(
        "SELECT student_no, student_name, final_score, teacher_comment FROM grades ORDER BY student_no LIMIT 5"
    )
    return render_lab(
        "labs/report_stacked.html",
        "report-stacked",
        month=month,
        rows=rows,
        message=message,
        error=error,
        sample_grades=sample_grades,
    )


@app.route("/labs/second-order", methods=["GET", "POST"])
def second_order():
    save_message = None
    report_rows = []
    current_filter = None
    error = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            filter_name = request.form.get("filter_name", "")
            department_filter = request.form.get("department_filter", "")
            run_statement(
                "INSERT INTO saved_filters (user_id, filter_name, department_filter) VALUES (%s, %s, %s)",
                (1, filter_name, department_filter),
            )
            save_message = "筛选器已保存。现在请到下方报表区触发它。"
        elif action == "run":
            saved = run_select(
                "SELECT filter_name, department_filter FROM saved_filters WHERE user_id = 1 ORDER BY filter_id DESC LIMIT 1"
            )
            if saved:
                current_filter = saved[0]["department_filter"]
                try:
                    if current_mode() == "safe":
                        report_rows = run_select(
                            "SELECT employee_id, full_name, department, title FROM employees WHERE department = %s ORDER BY full_name",
                            (current_filter,),
                        )
                    else:
                        sql = (
                            "SELECT employee_id, full_name, department, title FROM employees "
                            f"WHERE department = '{current_filter}' ORDER BY full_name"
                        )
                        report_rows = run_select(sql)
                except Exception as exc:
                    error = str(exc) if current_mode() == "vuln" else "报表筛选值非法。"
    saved_filters = run_select(
        "SELECT filter_id, filter_name, department_filter, created_at FROM saved_filters WHERE user_id = 1 ORDER BY filter_id DESC LIMIT 5"
    )
    return render_lab(
        "labs/second_order.html",
        "second-order",
        save_message=save_message,
        report_rows=report_rows,
        current_filter=current_filter,
        saved_filters=saved_filters,
        error=error,
    )


@app.route("/labs/leaderboard-sort")
def leaderboard_sort():
    sort = request.args.get("sort", "final_score")
    direction = request.args.get("dir", "DESC")
    limit = request.args.get("limit", "5")
    rows = []
    error = None
    try:
        if current_mode() == "safe":
            allowed_sort = {"student_no", "student_name", "class_name", "final_score"}
            allowed_dir = {"ASC", "DESC"}
            sort = sort if sort in allowed_sort else "final_score"
            direction = direction.upper() if direction.upper() in allowed_dir else "DESC"
            parsed_limit = max(1, min(int(limit), 20))
            sql = (
                "SELECT student_no, student_name, class_name, final_score FROM grades "
                f"ORDER BY {sort} {direction} LIMIT {parsed_limit}"
            )
            rows = run_select(sql)
        else:
            sql = (
                "SELECT student_no, student_name, class_name, final_score FROM grades "
                f"ORDER BY {sort} {direction} LIMIT {limit}"
            )
            rows = run_select(sql)
    except Exception as exc:
        error = str(exc) if current_mode() == "vuln" else "排序参数不合法。"
    return render_lab(
        "labs/leaderboard_sort.html",
        "leaderboard-sort",
        rows=rows,
        sort=sort,
        direction=direction,
        limit=limit,
        error=error,
    )


@app.route("/labs/grade-editor", methods=["GET", "POST"])
def grade_editor():
    affected_rows = None
    error = None
    if request.method == "POST":
        student_no = request.form.get("student_no", "")
        bonus_expr = request.form.get("bonus_expr", "0")
        remark = request.form.get("remark", "")
        try:
            if current_mode() == "safe":
                bonus_value = int(bonus_expr)
                if bonus_value < 0 or bonus_value > 15:
                    raise ValueError("补分范围必须在 0 到 15 之间")
                affected_rows = run_statement(
                    "UPDATE grades SET final_score = final_score + %s, teacher_comment = %s WHERE student_no = %s",
                    (bonus_value, remark[:80], student_no),
                )
            else:
                sql = (
                    "UPDATE grades SET final_score = final_score + "
                    f"{bonus_expr}, teacher_comment = '{remark}' WHERE student_no = '{student_no}'"
                )
                affected_rows = run_statement(sql)
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "更新请求不符合规则。"
    grades = run_select(
        "SELECT student_no, student_name, class_name, midterm, final_exam, final_score, teacher_comment FROM grades ORDER BY student_no"
    )
    return render_lab(
        "labs/grade_editor.html",
        "grade-editor",
        grades=grades,
        affected_rows=affected_rows,
        error=error,
    )


@app.route("/labs/api-json-sqli")
def api_json_sqli():
    return render_lab("labs/api_json_sqli.html", "api-json-sqli")


@app.route("/api/v1/orders/search", methods=["POST"])
def api_orders_search():
    mode = current_mode()
    payload = request.get_json(silent=True) or {}
    customer = payload.get("customer", "")
    min_total = str(payload.get("min_total", "0"))
    try:
        if mode == "safe":
            amount = Decimal(min_total)
            needle = f"%{customer}%"
            rows = run_select(
                "SELECT order_number, customer_name, total_amount, status FROM orders WHERE customer_name LIKE %s AND total_amount >= %s ORDER BY total_amount DESC LIMIT 10",
                (needle, amount),
            )
        else:
            sql = (
                "SELECT order_number, customer_name, total_amount, status FROM orders "
                f"WHERE customer_name LIKE '%{customer}%' AND total_amount >= {min_total} "
                "ORDER BY total_amount DESC LIMIT 10"
            )
            rows = run_select(sql)
        return jsonify({"mode": mode, "count": len(rows), "rows": rows})
    except (InvalidOperation, ValueError):
        return jsonify({"mode": mode, "error": "min_total 必须是数值。"}), 400
    except Exception as exc:
        message = str(exc) if mode == "vuln" else "请求格式错误。"
        return jsonify({"mode": mode, "error": message}), 400


@app.route("/labs/faux-fix", methods=["GET", "POST"])
def faux_fix():
    matched_user = None
    result = None
    error = None

    def weak_filter(value: str) -> str:
        sanitized = value
        for token in ["union", "select", " or ", "OR", "--", ";"]:
            sanitized = sanitized.replace(token, "")
        return sanitized

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            if current_mode() == "safe":
                rows = run_select(
                    "SELECT username, role, display_name FROM users WHERE username = %s AND password = %s LIMIT 1",
                    (username, password),
                )
            else:
                filtered_user = weak_filter(username)
                filtered_password = weak_filter(password)
                sql = (
                    "SELECT username, role, display_name FROM users "
                    f"WHERE username = '{filtered_user}' AND password = '{filtered_password}' LIMIT 1"
                )
                rows = run_select(sql)
            result = "登录成功" if rows else "登录失败"
            matched_user = rows[0] if rows else None
        except Exception as exc:
            error = str(exc) if current_mode() == "vuln" else "请求处理失败。"
    return render_lab("labs/faux_fix.html", "faux-fix", matched_user=matched_user, result=result, error=error)


@app.route("/labs/orm-misuse")
def orm_misuse():
    category = request.args.get("category", "Hardware")
    rows = []
    error = None
    try:
        with engine.connect() as connection:
            if current_mode() == "safe":
                query = text(
                    "SELECT product_id, sku, name, category, price FROM products WHERE category = :category ORDER BY price DESC"
                )
                result = connection.execute(query, {"category": category})
            else:
                query = text(
                    "SELECT product_id, sku, name, category, price FROM products "
                    f"WHERE category = '{category}' ORDER BY price DESC"
                )
                result = connection.execute(query)
            rows = [dict(row._mapping) for row in result]
    except Exception as exc:
        error = str(exc) if current_mode() == "vuln" else "查询参数不合法。"
    return render_lab("labs/orm_misuse.html", "orm-misuse", rows=rows, category=category, error=error)


if __name__ == "__main__":
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=False)
