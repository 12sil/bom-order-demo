"""业务常量：所有页面统一引用，避免各页面重复定义规则。"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
# 数据路径以程序所在目录为基准，不受启动命令所在目录影响。
# 可在服务器上设置 BOM_DATA_DIR 指向持久化磁盘。
DATA_DIR = Path(os.getenv("BOM_DATA_DIR", str(ROOT / "data"))).resolve()
LOGISTICS_DAYS = 3  # 用户指定：预留 3 个自然日物流时间，非工作日。
MAX_FILE_MB = 20
MAX_PDF_PAGES = 12
STATUSES = ("未发货", "已发货", "已送达", "已取消")
