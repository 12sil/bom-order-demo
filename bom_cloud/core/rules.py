"""严格的日期、数量校验和发货预警规则。

必须发货日 = 客户要求的最终交付日 - 3 个自然日。
不要使用下单日期、实际送货日期、工作日算法替代这个计算。
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from config import LOGISTICS_DAYS, STATUSES

TODAY = "🔥今日必须发出（物流倒计时）"
URGENT = "⚠️紧急备货，即将发货"
OVERDUE = "❌发货逾期"
NORMAL = "🟢正常订单"


def today_china() -> date:
    """统一使用北京时间，避免服务器在 UTC 时区造成预警差一天。"""
    return datetime.now(timezone(timedelta(hours=8))).date()


def timestamp() -> str:
    """持久化日志保留含时区的时间戳。"""
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def parse_date(value) -> date:
    """只接受真实完整日期；缺少年份或 2 月 30 日不能静默修正。"""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("日期必须是完整有效日期，例如 2026-09-20。") from None


def quantity_text(value) -> str:
    """数量采用十进制，兼容件、米、千克等计量，不使用浮点误差累加。"""
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError("订单数量必须是大于 0 的数字。") from None
    if not number.is_finite() or number <= 0 or number > 100000000:
        raise ValueError("订单数量必须大于 0，且不超过一亿。")
    if number.as_tuple().exponent < -3:
        raise ValueError("订单数量最多保留三位小数。")
    return format(number.normalize(), "f")


def required_ship_date(deadline) -> date:
    """唯一的系统发货日计算入口，自动处理跨月、跨年和闰年。"""
    result = parse_date(deadline) - timedelta(days=LOGISTICS_DAYS)
    return result


def warning(deadline, status="未发货", today=None) -> dict:
    """先排除已履约/取消订单，再按互斥区间判断，今日不能被 <=3 天覆盖。"""
    if status not in STATUSES:
        raise ValueError("未知订单状态。")
    ship = required_ship_date(deadline)
    days = (ship - (parse_date(today) if today else today_china())).days
    if status != "未发货":
        label = {"已发货": "🚚已发货，运输中", "已送达": "✅已完成交付", "已取消": "—已取消"}[status]
        return {"label": label, "level": "closed", "days": days, "ship_date": ship.isoformat(), "rank": 4}
    if days < 0:
        label, level, rank = OVERDUE, "overdue", 0
    elif days == 0:
        label, level, rank = TODAY, "today", 1
    elif 1 <= days <= 3:
        label, level, rank = URGENT, "urgent", 2
    else:
        label, level, rank = NORMAL, "normal", 3
    return {"label": label, "level": level, "days": days, "ship_date": ship.isoformat(), "rank": rank}
