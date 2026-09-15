"""板块一：双向关联查询。仅展示，不保存、不修改任何业务数据。"""
import streamlit as st
from core.query import customer_trace, product_trace, order_history
from views.common import header, order_table, history_table, product_details


def render(store):
    header("01 / TRACEABILITY", "双向数据查询", "客户 → 产品 → 订单；产品 → 客户 → 历史记录。此页面为纯查询。")
    data = store.read()
    keyword = st.text_input("快速检索", placeholder="输入客户名称、产品名称或产品编码")
    tab_c, tab_p = st.tabs(["👥 从客户追溯", "📦 从产品反查"])
    with tab_c:
        customers = [c for c in data["customers"] if not keyword or keyword.casefold() in c["name"].casefold()]
        if not customers:
            st.info("没有匹配客户，请调整检索内容或先建立客户档案。")
        else:
            selected = st.selectbox("选择客户", customers, format_func=lambda c: c["name"], key="trace_customer")
            st.write(f"联系人：{selected['contact'] or '未填写'}  |  电话：{selected['phone'] or '未填写'}")
            st.caption(f"地址：{selected['address'] or '未填写'}")
            orders = customer_trace(data, selected["id"])
            a, b, c = st.columns(3)
            a.metric("历史订单", len(orders))
            b.metric("采购产品种类", len({o["product_id"] for o in orders}))
            c.metric("涉及订单月份", len({o["order_month"] for o in orders}))
            st.subheader("所有历史订单")
            order_table(orders)
            # 产品展开详情与产品反查共用同一份资料，避免数据割裂。
            with st.expander("查看该客户涉及的产品与 BOM 资料"):
                ids = {o["product_id"] for o in orders}
                for product in data["products"]:
                    if product["id"] in ids:
                        product_details(product, store)
                        st.divider()
            with st.expander("送货与状态追溯记录"):
                history_table(order_history(data, {o["id"] for o in orders}))
    with tab_p:
        products = [p for p in data["products"] if not keyword or keyword.casefold() in (p["name"] + p["code"]).casefold()]
        if not products:
            st.info("没有匹配产品，请调整检索内容或先建立产品资料。")
        else:
            selected = st.selectbox("选择产品", products, format_func=lambda p: f"{p['code']} · {p['name']}", key="trace_product")
            orders = product_trace(data, selected["id"])
            st.markdown("#### 哪些客户采购过？")
            ids = {o["customer_id"] for o in orders}
            customers = [c for c in data["customers"] if c["id"] in ids]
            if customers:
                st.dataframe([{"客户": c["name"], "联系人": c["contact"], "电话": c["phone"],
                               "历史订单数": sum(o["customer_id"] == c["id"] for o in orders)} for c in customers],
                              hide_index=True, use_container_width=True)
            else:
                st.info("该产品暂无采购记录。")
            st.subheader("该产品的所有历史订单")
            order_table(orders)
            with st.expander("送货与状态追溯记录", expanded=False):
                history_table(order_history(data, {o["id"] for o in orders}))
            with st.expander("查看产品全套 BOM 资料"):
                product_details(selected, store)
