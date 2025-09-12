import csv
import json
import os
from typing import Dict, List, Optional

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


# 从 Akshare 导出的 CSV 读取 {名称: 最新价} 映射
def load_name_price_from_csv(csv_path: str) -> Dict[str, float]:
    name_to_price: Dict[str, float] = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("名称")
            price_text = row.get("最新价")
            if not name or price_text is None:
                continue
            try:
                # 强制转换为 float，过滤异常值
                price = float(str(price_text).strip())
                name_to_price[name] = price
            except ValueError:
                # 跳过无法解析的价格
                continue
    return name_to_price


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"\'")
                # 不覆盖已存在的环境变量
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # 遇到异常时忽略，不影响主流程
        pass


def build_records(name_to_price: Dict[str, float], field_key: str) -> List[AppTableRecord]:
    # 建立飞书多维表格中 record_id 与股票名称的映射
    targets = [
        {"record_id": "rec25ORoaS06hp", "name": "通富微电"},
        {"record_id": "rec25ORoaS06yw", "name": "英维克"},
        {"record_id": "rec25ORoaS06IZ", "name": "拓尔思"},
        {"record_id": "rec25ORoaS06Sp", "name": "两面针"},
        {"record_id": "rec25ORoaS0714", "name": "科大讯飞"},
        {"record_id": "rec25ORoaS078B", "name": "金山办公"},
        {"record_id": "rec25ORoaS07fT", "name": "中科曙光"},
        {"record_id": "rec25ORoaS07ns", "name": "科大国创"},
    ]

    records: List[AppTableRecord] = []
    for t in targets:
        name = t["name"]
        record_id = t["record_id"]
        price = name_to_price.get(name)
        if price is None:
            lark.logger.warning(f"未在 CSV 中找到 {name} 的最新价，跳过该记录: {record_id}")
            continue
        rec = (
            AppTableRecord.builder()
            .record_id(record_id)
            # 仅更新价格字段，避免无意义覆盖名称
            .fields({field_key: price})
            .build()
        )
        records.append(rec)
    return records


# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
def main():
    # 尝试加载 .env 文件中的配置（若存在）
    load_env_file()
    # 读取 CSV（注意文件名中包含单引号）
    csv_path = "data/'all_stock.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"未找到价格文件: {csv_path}")

    name_to_price = load_name_price_from_csv(csv_path)
    if not name_to_price:
        raise RuntimeError("CSV 未解析到任何价格数据，请检查文件格式与编码")

    # 读取字段配置，优先使用 ID -> 映射到字段名（避免使用 field_key 参数）
    target_field_id = os.getenv("TARGET_FIELD_ID")
    default_field_name = os.getenv("TARGET_FIELD_NAME", "Current Price")

    # 创建 client（沿用现有 user_access_token 方案）
    client = (
        lark.Client.builder()
        .enable_set_token(True)
        .log_level(lark.LogLevel.DEBUG)
        .build()
    )

    # 从环境变量读取配置，若不存在则退回到默认值（与原脚本一致）
    app_token = os.getenv("APP_TOKEN", "U3iYbe8cGaBrLEso6jMctMVgnVb")
    table_id = os.getenv("TABLE_ID", "tbl29O0osz3dn74L")

    # 统一请求选项（优先从环境变量读取 user_access_token）
    user_access_token = os.getenv(
        "USER_ACCESS_TOKEN",
        "u-cmskeyx6591byAdcRjQIiO11hVjl052jWE00kk0ww914",
    )
    option = (
        lark.RequestOption.builder()
        .user_access_token(user_access_token)
        .build()
    )

    def resolve_field_name_by_id(client: lark.Client, app_token: str, table_id: str, field_id: str) -> Optional[str]:
        try:
            req = ListAppTableFieldRequest.builder().app_token(app_token).table_id(table_id).build()
            resp: ListAppTableFieldResponse = client.bitable.v1.app_table_field.list(req, option)
            if not resp.success():
                lark.logger.warning(
                    f"获取字段列表失败，使用默认字段名。code={resp.code}, msg={resp.msg}, log_id={resp.get_log_id()}"
                )
                return None
            items = []
            try:
                items = resp.data.items or []
            except Exception:
                pass
            for it in items:
                fid = getattr(it, "field_id", None) or getattr(it, "id", None)
                fname = getattr(it, "field_name", None) or getattr(it, "name", None)
                if fid == field_id:
                    return fname
            lark.logger.warning(f"未在字段列表中找到字段ID: {field_id}，使用默认字段名")
            return None
        except Exception as e:
            lark.logger.warning(f"解析字段名异常: {e}")
            return None

    field_name_for_update = default_field_name
    if target_field_id:
        resolved = resolve_field_name_by_id(client, app_token, table_id, target_field_id)
        if resolved:
            field_name_for_update = resolved

    records = build_records(name_to_price, field_name_for_update)
    if not records:
        lark.logger.warning("没有可更新的记录，可能所有目标名称都未在 CSV 中找到")
        return

    request: BatchUpdateAppTableRecordRequest = (
        BatchUpdateAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .user_id_type("user_id")
        .request_body(
            BatchUpdateAppTableRecordRequestBody.builder()
            .records(records)
            .build()
        )
        .build()
    )

    # 发起请求（保留原来的 user_access_token 用法）
    response: BatchUpdateAppTableRecordResponse = client.bitable.v1.app_table_record.batch_update(request, option)

    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.batch_update failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        )
        return

    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    main()
