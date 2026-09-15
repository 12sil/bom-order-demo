"""板块三：客户订单文件智能导入。独立页面，识别与写入结果明确展示。"""
from config import ROOT
import pandas as pd
import streamlit as st
from core.recognition import recognize_local, file_hash, validation_errors, FIELDS
from core.rules import required_ship_date
from core.service import import_orders
from views.common import header

LABELS = {"customer_name": "客户名称", "product_name": "产品名称", "product_code": "产品编码（可选）", "quantity": "订单数量", "unit": "单位", "delivery_deadline": "客户交付截止日期"}


def render(store):
    header("03 / DOCUMENT INTELLIGENCE", "客户订单文件智能导入", "截图、图片、PDF → 字段识别 → 关联档案 → 自动回推发货日 → 临时 CSV 演示保存。")
    st.markdown('<div class="flow">01 上传文件　→　02 智能识别　→　03 规则校验　→　04 自动入单</div>', unsafe_allow_html=True)
    engine = "本地 OCR（免费）"
    st.caption("免费神经网络 OCR + 字段提取。只上传虚构订单；模糊或缺失字段需要核对。本展示版不调用付费 AI 接口。")
    sample = ROOT / "samples" / "客户订单样例.png"
    if sample.exists():
        st.download_button("下载虚构订单样例图片", sample.read_bytes(), file_name="客户订单样例.png", mime="image/png")
    uploaded = st.file_uploader("上传客户订单文件", type=["png", "jpg", "jpeg", "webp", "pdf"], help="单文件不超过 20MB，PDF 最多 12 页。")
    if uploaded is None:
        st.info("请上传虚构订单样例。完整字段可一键识别入单，无需手动输入。")
        return
    raw = uploaded.getvalue()
    digest = file_hash(raw)
    # 使用文件内容与数据空间共同命名状态，切换演示/正式数据不会复用旧导入状态。
    result_key = "recognition:" + str(store.root) + ":" + digest
    existing = next((x for x in store.read()["imports"] if x["file_hash"] == digest), None)
    if existing:
        st.success(f"该文件已入库，关联订单：{existing['order_ids']}。已阻止重复入单。")
        return
    automatic = st.checkbox("识别通过后自动生成订单", value=True, help="有缺失、低清晰度或冲突时停止自动保存，保留结果供核对。")
    if st.button("识别并自动入单" if automatic else "开始识别", type="primary", use_container_width=True):
        try:
            with st.spinner("正在识别文字与订单字段…"):
                result = recognize_local(raw, uploaded.name)
            st.session_state[result_key] = result
            if automatic and not result["issues"]:
                ids = import_orders(store, result["rows"], digest, uploaded.name, raw, result["engine"], result["raw_text"])
                st.success(f"已自动生成 {len(ids)} 笔订单，发货日期已按交付日期减 3 天计算。")
                for row in result["rows"]:
                    st.write(f"{row['customer_name']} · {row['product_name']} · {row['quantity']} {row['unit']}　｜　必须发货日 {required_ship_date(row['delivery_deadline'])}")
                st.caption("订单已保存，可前往预警看板或双向查询查看。")
                return
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(str(exc))
    result = st.session_state.get(result_key)
    if result:
        st.subheader("识别结果与核对")
        for issue in result["issues"]:
            st.warning(str(issue))
        with st.expander("查看识别原文与字段依据"):
            st.text(result["raw_text"] or "未提取到文字。")
            if result["ocr_score"] is not None:
                st.caption(f"最低文字识别分数：{result['ocr_score']:.2f}，仅反映 OCR 字形识别，不代表整张订单准确率。")
        frame = pd.DataFrame([{k: row.get(k, "") for k in FIELDS} for row in result["rows"]])
        edited = st.data_editor(frame, column_config={k: st.column_config.TextColumn(v) for k, v in LABELS.items()}, hide_index=True,
                                num_rows="dynamic", use_container_width=True, key="editor:" + result_key)
        confirmed = st.checkbox("已核对客户、产品、数量及客户最终交付日期", key="confirm:" + result_key)
        if st.button("确认结果并入库", disabled=not confirmed, type="primary"):
            try:
                rows = edited.fillna("").to_dict("records")
                errors = validation_errors(rows)
                if errors:
                    raise ValueError("\n".join(errors))
                ids = import_orders(store, rows, digest, uploaded.name, raw, result["engine"], result["raw_text"])
                st.success(f"已保存 {len(ids)} 笔订单；刷新或重复上传不会重复入单。")
            except (ValueError, OSError) as exc:
                st.error(str(exc))
