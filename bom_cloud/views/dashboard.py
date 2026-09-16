"""板块二：智能发货预警。预警清单独立于月份筛选，防止跨月漏单。"""
import streamlit as st
from core.rules import today_china
from core.query import enriched_orders, shipped_summary
from core.service import update_status
from views.common import header, order_table, saved, notify


def render(store):
    header("02 / DELIVERY CONTROL", "智能订单预警看板", "客户最终交付日期 − 3 个自然日 = 实际必须发货日期。")
    notify()
    data = store.read()
    orders = enriched_orders(data)
    # 顶部三个数字按全部月份的未发货订单统计，三类互斥，避免重复计数。
    high, near, safe = st.columns(3)
    high.metric("🔴 高风险", sum(o["level"] in ("overdue", "today") for o in orders))
    near.metric("🟠 临期", sum(o["level"] == "urgent" for o in orders))
    safe.metric("🟢 安全", sum(o["level"] == "normal" for o in orders))
    st.caption("全部月份 · 仅未发货：高风险 = 逾期或今日必须发货；临期 = 1～3 天内必须发货；安全 = 超过 3 天。")
    today = today_china()
    left, right = st.columns([3, 1])
    with left:
        st.info(f"📅 北京时间 {today.isoformat()}　｜　物流预留 3 天　｜　订单月按客户交付月份归属")
    with right:
        if st.button("刷新预警", use_container_width=True):
            st.rerun()
    months = sorted({today.strftime("%Y-%m")} | {o["order_month"] for o in orders}, reverse=True)
    month = st.selectbox("全月订单总览 · 选择月份", months, index=months.index(today.strftime("%Y-%m")))
    monthly = [o for o in orders if o["order_month"] == month]
    due = [o for o in orders if o["level"] == "today"]
    urgent = [o for o in orders if o["level"] == "urgent"]
    late = [o for o in orders if o["level"] == "overdue"]
    a, b, c, d = st.columns(4)
    a.metric("本月订单总数", len(monthly))
    b.metric("今日必须发货 · 全部月份", len(due))
    c.metric("3 天内紧急备货 · 全部月份", len(urgent))
    d.metric("发货逾期 · 全部月份", len(late))
    st.subheader("🔥 今日必须发货清单")
    st.caption("独立清单，包含全部月份。未发货且今天等于系统计算发货日，必须今天发出。")
    order_table(due, "今天没有必须发货的订单。")
    if due:
        with st.expander("今日订单 · 一键确认已发货"):
            for order in due:
                text, action = st.columns([4, 1])
                text.write(f"{order['current_customer']} · {order['current_product']} · {order['quantity']} {order['unit']}")
                if action.button("确认已发货", key=f"ship_{order['id']}", use_container_width=True):
                    try:
                        update_status(store, order["id"], "已发货", today, note="今日清单一键确认发货", expected_status="未发货")
                        saved("已记录实际发货日期；该订单已移出未发货预警。")
                    except ValueError as exc:
                        st.error(str(exc))
    with st.expander(f"❌ 发货逾期清单 · {len(late)} 笔", expanded=bool(late)):
        order_table(late, "没有发货逾期订单。")
    with st.expander(f"⚠️ 紧急待发货清单 · {len(urgent)} 笔", expanded=True):
        st.caption("距离必须发货日为 1、2、3 天；今日与逾期订单在各自清单展示。")
        order_table(urgent, "未来 3 天暂无紧急备货订单。")
    st.divider()
    st.subheader(f"{month} · 全月订单总览")
    q = st.text_input("筛选本月订单", placeholder="客户 / 产品 / 产品编码 / 订单编号")
    filtered = [o for o in monthly if q.casefold() in " ".join((o["current_customer"], o["current_product"], o["product_code"], o["id"])).casefold()]
    order_table(filtered, "所选月份没有匹配订单。")
    with st.expander("客户月度出货统计 · 按实际发货月份"):
        summary = shipped_summary(data, month)
        if summary:
            st.dataframe(summary, hide_index=True, use_container_width=True)
        else:
            st.info("该月还没有实际出货记录。")
        st.caption("以实际发货日期统计，已取消订单排除；不同计量单位分开汇总。")
