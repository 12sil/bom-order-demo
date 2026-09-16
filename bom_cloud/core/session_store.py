"""让演示订单的会话副本与 CSV 保持同步，所有页面仍使用统一存储接口。"""
from contextlib import contextmanager
from copy import deepcopy
import streamlit as st
from core.storage import CsvStore


class SessionCsvStore(CsvStore):
    """CSV 是一致性来源；成功读取或提交后才更新 session_state，避免半写入。"""

    def read(self):
        data = super().read()
        st.session_state["orders"] = deepcopy(data["orders"])
        return data

    @contextmanager
    def transaction(self):
        with super().transaction() as data:
            yield data
        # 只有事务成功退出才同步，新增、导入、发货和重置都会经过这里。
        st.session_state["orders"] = deepcopy(data["orders"])
