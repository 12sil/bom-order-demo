"""产品资料库：图片、介绍、规格、BOM 清单、配套检查表集中维护。"""
import streamlit as st
from core.service import save_product, save_image
from views.common import header, product_details, notify, saved


def render(store):
    header("MASTER DATA / PRODUCTS", "产品资料库", "从一个产品，查到完整资料、物料清单与配套检查要求。")
    notify()
    products = store.read()["products"]
    query = st.text_input("搜索产品", placeholder="产品名称 / 产品编码")
    filtered = [p for p in products if query.casefold() in (p["name"] + p["code"]).casefold()]
    if not filtered:
        st.info("暂无匹配产品，可在下方新增资料。")
    for product in filtered:
        with st.expander(f"📦 {product['name']}　|　{product['code']}　|　{product['unit']}"):
            product_details(product, store)
    st.divider()
    mode = st.radio("资料操作", ["新增产品", "修改产品资料"], horizontal=True)
    row = {}
    if mode == "修改产品资料":
        if not products:
            st.info("暂无可修改产品。")
            return
        row = st.selectbox("选择产品资料", products, format_func=lambda p: f"{p['code']} · {p['name']}")
    with st.form("product_form"):
        a, b, c = st.columns([2, 2, 1])
        values = {}
        values["name"] = a.text_input("产品名称 *", row.get("name", ""), max_chars=100)
        values["code"] = b.text_input("产品编码 *", row.get("code", ""), max_chars=100)
        values["unit"] = c.text_input("计量单位 *", row.get("unit", "件"), max_chars=15)
        image = st.file_uploader("上传产品图片（可选）", type=["png", "jpg", "jpeg", "webp"])
        values["description"] = st.text_area("产品介绍", row.get("description", ""), max_chars=6000)
        a, b = st.columns(2)
        values["specs"] = a.text_area("规格参数", row.get("specs", ""), placeholder="例如：尺寸 120×80mm；材质 铝合金；工作电压 12V", height=130, max_chars=6000)
        values["checklist"] = b.text_area("配套检查表（每行一项）", row.get("checklist", ""), placeholder="外观无划痕\n配件数量齐全\n通电测试合格", height=130, max_chars=6000)
        values["bom"] = st.text_area("BOM 物料清单", row.get("bom", ""), placeholder="每行一项：物料编码 | 物料名称 | 单件用量 | 单位 | 规格\nM001 | 外壳 | 1 | 件 | 铝合金", max_chars=12000)
        submit = st.form_submit_button("保存产品资料", type="primary")
    if submit:
        try:
            values["image_path"] = save_image(store, image.getvalue()) if image else row.get("image_path", "")
            save_product(store, values, row.get("id"))
            saved("产品全套资料已保存。")
        except ValueError as exc:
            st.error(str(exc))
