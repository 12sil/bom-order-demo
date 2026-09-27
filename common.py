"""共用页面元素：只负责展示，业务计算留在 core 中。"""
from pathlib import Path
import html
import pandas as pd
import streamlit as st
from core.rules import TODAY, URGENT, OVERDUE


def header(kicker, title, subtitle):
    st.markdown(f'<div class="kicker">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def order_frame(orders):
    return pd.DataFrame([{"订单编号": o["id"], "客户": o["current_customer"], "产品": o["current_product"],
                          "产品编码": o["product_code"], "订单月": o["order_month"], "数量": o["quantity"], "单位": o["unit"],
                          "客户交付日期": o["delivery_deadline"], "系统计算发货日": o["ship_date"], "预警状态": o["label"],
                          "订单状态": o["status"], "实际发货日期": o["shipped_date"], "实际送达日期": o["delivered_date"]}
                         for o in orders])


def order_table(orders, empty="暂无订单记录。"):
    if not orders:
        st.info(empty)
        return
    frame = order_frame(orders)
    def paint(row):
        colors = {TODAY: "#fff1e3", URGENT: "#fff9e3", OVERDUE: "#ffe9ee"}
        color = colors.get(row["预警状态"], "")
        return [f"background-color: {color}; color: #18253f" if color else "" for _ in row]
    st.dataframe(frame.style.apply(paint, axis=1), hide_index=True, use_container_width=True)


def history_table(history):
    if not history:
        st.info("暂无送货或状态变更记录。")
        return
    st.dataframe(pd.DataFrame(history).rename(columns={"order_id": "订单编号", "from_status": "原状态", "to_status": "新状态",
        "shipped_date": "实际发货日期", "delivered_date": "实际送达日期", "note": "变更说明", "created_at": "记录时间"}).drop(columns="id"),
        hide_index=True, use_container_width=True)


def product_details(product, store):
    left, right = st.columns([1, 2])
    with left:
        relative = product.get("image_path", "")
        path = (store.root / relative).resolve() if relative else None
        if path and path.is_relative_to(store.root) and path.is_file():
            st.image(str(path), use_container_width=True)
        else:
            st.markdown('<div class="product-placeholder">📦<p>暂未上传产品图片</p></div>', unsafe_allow_html=True)
    with right:
        st.subheader(product["name"])
        st.caption(f"产品编码：{product['code']}  ·  计量单位：{product['unit']}")
        st.write(product["description"] or "尚未填写产品介绍。")
        st.markdown("**规格参数**")
        st.text(product["specs"] or "尚未填写规格参数。")
    a, b = st.columns(2)
    with a:
        st.markdown("#### BOM 物料清单")
        st.text(product.get("bom") or "尚未填写物料清单。")
    with b:
        st.markdown("#### 配套检查表")
        lines = [s.strip() for s in product["checklist"].splitlines() if s.strip()]
        for i, line in enumerate(lines, 1):
            st.write(f"{i}. {line}")
        if not lines:
            st.caption("尚未填写检查项目。")


def notify():
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))


def saved(message):
    st.session_state["flash"] = message
    st.rerun()
