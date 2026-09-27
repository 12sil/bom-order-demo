"""独立竞赛演示数据，永远不写入正式业务空间。"""
from datetime import timedelta
from core.rules import timestamp, today_china
from core.service import _add_order, uid


def reset_demo_orders(store):
    """用五条虚构订单替换当前订单；相对今天生成日期，比赛当天也能展示预警。

    配置依次为：客户序号、产品序号、数量、距离必须发货日的天数。
    可在此修改五条样例；最终交付日始终等于必须发货日加三天。
    """
    samples = [(0, 0, 120, -1), (1, 1, 60, 0), (2, 2, 200, 1),
               (0, 1, 80, 3), (1, 0, 150, 8)]
    today = today_china()
    with store.transaction() as data:
        # 保留档案；只重置订单相关表，避免残留历史记录指向旧订单。
        data["orders"] = []
        data["history"] = []
        data["imports"] = []
        for customer, product, quantity, offset in samples:
            _add_order(data, {
                "customer_id": data["customers"][customer % len(data["customers"])]["id"],
                "product_id": data["products"][product % len(data["products"])]["id"],
                "quantity": quantity,
                "delivery_deadline": today + timedelta(days=offset + 3),
                "notes": "一键加载的虚构演示订单",
            }, source="演示数据")


def seed_demo(store):
    """只在全新演示空间首次创建，后续刷新/重启都保留用户修改。"""
    with store.transaction() as data:
        if any(data.values()):
            return
        customers = [("杭州启晨科技有限公司", "陈经理", "0571-0000-0001", "杭州 · 滨江区"),
                     ("苏州云帆智造有限公司", "林女士", "0512-0000-0002", "苏州 · 工业园区"),
                     ("宁波森合文创有限公司", "周先生", "0574-0000-0003", "宁波 · 鄞州区")]
        for name, contact, phone, address in customers:
            data["customers"].append({"id": uid("C"), "name": name, "contact": contact, "phone": phone, "address": address, "notes": "竞赛演示虚构客户", "created_at": timestamp()})
        products = [("BOM-L01", "智能氛围灯套件", "套", "可调色温、模块化组装的桌面照明套件。", "功率：5W\n尺寸：120 × 80 × 180 mm\n供电：USB-C 5V", "M01 | 灯罩 | 1 | 件 | 磨砂 PC\nM02 | LED 板 | 1 | 块 | 5W\nM03 | 电源线 | 1 | 根 | USB-C"),
                    ("BOM-D02", "数字展示支架", "件", "适用于展览陈列与数字媒体互动终端的桌面支架。", "材质：铝合金\n适用尺寸：7-13 英寸\n颜色：深空灰", "M10 | 底座 | 1 | 件 | 铝合金\nM11 | 转轴 | 2 | 件 | 不锈钢\nM12 | 防滑垫 | 4 | 个 | 硅胶"),
                    ("BOM-S03", "互动感应模组", "套", "用于交互装置的红外感应与信号控制模组。", "工作电压：12V\n感应距离：0.1-1m\n输出：数字信号", "M20 | 主控板 | 1 | 块 | MCU\nM21 | 传感器 | 2 | 个 | 红外\nM22 | 连接线 | 1 | 根 | 4 芯")]
        for code, name, unit, desc, specs, bom in products:
            data["products"].append({"id": uid("P"), "code": code, "name": name, "unit": unit, "description": desc,
                                     "specs": specs, "bom": bom, "checklist": "核对物料与数量\n外观检查无划痕\n功能测试通过\n标签与包装齐全", "image_path": "", "created_at": timestamp()})
        # offset 指必须发货日相对今天；最终交付日必须再加 3 天。
        for i, offset in enumerate((0, 0, 1, 3, -2, 8, 12, -4)):
            today = today_china()
            oid = _add_order(data, {"customer_id": data["customers"][i % 3]["id"], "product_id": data["products"][i % 3]["id"],
                                    "quantity": (120, 60, 200, 80, 40, 150, 100, 50)[i],
                                    "delivery_deadline": today + timedelta(days=offset + 3), "notes": "竞赛演示订单"}, source="演示数据")
            if i == 7:
                row = next(o for o in data["orders"] if o["id"] == oid)
                row.update(status="已送达", shipped_date=(today - timedelta(days=4)).isoformat(), delivered_date=(today - timedelta(days=1)).isoformat())
                data["history"].append({"id": uid("H"), "order_id": oid, "from_status": "未发货", "to_status": "已送达", "shipped_date": row["shipped_date"],
                                        "delivered_date": row["delivered_date"], "note": "演示历史履约记录", "created_at": timestamp()})
