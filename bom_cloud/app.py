"""序单 BOM · Streamlit 主入口。

运行：python -m streamlit run app.py
主入口仅负责导航、样式及数据空间；业务规则和 CSV 读写放在 core 中。
三大业务板块独立，基础档案维护放在辅助导航组。此包仅用于线上比赛演示。
"""
from functools import partial
import logging
import tempfile
import uuid
from pathlib import Path
import streamlit as st
from filelock import Timeout
from config import ROOT
from core.storage import StorageError
from core.session_store import SessionCsvStore
from core.demo import seed_demo, reset_demo_orders
from views import dashboard, trace, importer, orders, customers, products

st.set_page_config(page_title="序单 BOM · 智能订单管理", page_icon="📦", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>" + (ROOT / "assets/style.css").read_text(encoding="utf-8-sig") + "</style>", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("# 📦 序单 BOM")
    st.caption("小微企业 · 订单与产品客户管理")
    # 线上包固定为演示模式，不提供进入真实业务空间的入口。
    demo = True
    st.caption("🟠 演示空间 · 虚构样例" if demo else "🔵 正式业务空间")
    st.divider()
try:
    # 每个浏览器会话使用独立演示目录，避免评委互相修改同一份样例。
    if "demo_session" not in st.session_state:
        st.session_state.demo_session = uuid.uuid4().hex
    demo_root = Path(tempfile.gettempdir()) / "bom_competition_sessions" / st.session_state.demo_session
    store = SessionCsvStore(demo_root)
    if demo:
        seed_demo(store)
    with st.sidebar:
        # 仅覆盖当前浏览器会话的演示订单，不影响其他访客和客户/产品档案。
        st.caption("加载样例会替换当前会话全部订单及其送货、导入记录。")
        if st.button("一键加载演示数据", key="load_demo", use_container_width=True):
            reset_demo_orders(store)
            st.success("已加载 5 条演示订单。")
except (StorageError, OSError, Timeout) as exc:
    st.error(f"无法打开数据目录：{exc}")
    st.stop()

# Streamlit 原生多页导航：每个页面一个 render 函数，便于单独修改和测试。
pages = {
    "三大独立业务模块": [
        st.Page(partial(trace.render, store), title="① 双向数据查询", icon="🔎", url_path="trace"),
        st.Page(partial(dashboard.render, store), title="② 智能发货预警", icon="📊", url_path="dashboard", default=True),
        st.Page(partial(importer.render, store), title="③ 订单文件智能导入", icon="✨", url_path="import"),
    ],
    "基础资料与业务维护": [
        st.Page(partial(orders.render, store), title="手动订单 / 状态管理", icon="📝", url_path="orders"),
        st.Page(partial(customers.render, store), title="客户档案", icon="👥", url_path="customers"),
        st.Page(partial(products.render, store), title="产品 BOM 资料库", icon="📦", url_path="products"),
    ],
}
page = st.navigation(pages)
with st.sidebar:
    st.divider()
    st.caption("免费比赛展示 · 临时演示数据")
    st.caption("最终交付日 − 3 天 = 必须发货日")
if demo:
    st.info("比赛演示版：仅使用虚构样例。操作保存在当前会话；刷新、新会话或服务重启后可能重置，请勿录入真实业务资料。")
try:
    page.run()
except (StorageError, OSError, Timeout) as exc:
    logging.exception("数据操作失败")
    st.error(f"数据暂时不可用：{exc}。已有快照不会被覆盖，请检查磁盘和文件占用后重试。")
