"""板块二：智能发货预警。预警清单独立于月份筛选，防止跨月漏单。"""
import streamlit as st
import pandas as pd
import plotly.express as px
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
    st.markdown("#### 📊 订单预警分布概览")
    chart = pd.DataFrame({"订单数量": [
        sum(o["level"] in ("overdue", "today") for o in orders),
        sum(o["level"] == "urgent" for o in orders),
        sum(o["level"] == "normal" for o in orders),
    ]}, index=["高风险", "临期", "安全"])
    st.bar_chart(chart, y="订单数量", color="#3158dd", height=260)
    # 与数字看板使用相同口径；无未发货订单时不绘制误导性的空圆环。
    ring_col, trend_col = st.columns(2)
    with ring_col:
        st.markdown("#### 红黄绿 · 预警状态占比")
        if chart["订单数量"].sum():
            fig = px.pie(chart.reset_index(names="状态"), names="状态", values="订单数量",
                         hole=.65, color="状态", color_discrete_map={
                             "高风险": "#e45756", "临期": "#eebd36", "安全": "#35a778"})
            fig.update_traces(textinfo="label+percent", hovertemplate="%{label}：%{value} 笔<extra></extra>")
            fig.update_layout(height=320, margin=dict(l=15, r=15, t=20, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="risk_ring")
        else:
            st.info("暂无未发货订单。")
    with trend_col:
        st.markdown("#### 月度订单分布")
        # 按交付月份统计订单笔数；补齐中间空月份，跨年也按日期排序。
        active = [o for o in orders if o["status"] != "已取消"]
        st.caption("按客户交付月份统计订单笔数，排除已取消订单；不受下方月份筛选影响。")
        if active:
            counts = pd.Series([o["order_month"] for o in active]).value_counts().sort_index()
            months_all = pd.period_range(counts.index.min(), counts.index.max(), freq="M").astype(str)
            trend = counts.reindex(months_all, fill_value=0).rename_axis("月份").reset_index(name="订单笔数")
            fig = px.line(trend, x="月份", y="订单笔数", markers=True,
                          color_discrete_sequence=["#3158dd"])
            fig.update_xaxes(type="category")
            fig.update_yaxes(rangemode="tozero", dtick=1)
            fig.update_layout(height=320, margin=dict(l=15, r=15, t=20, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, key="monthly_trend")
        else:
            st.info("暂无可统计订单。")
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
