#!/usr/bin/env python3
"""
验证飞书表格更新结果
"""

import os
import json
import time
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


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
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"加载.env文件失败: {e}")


def verify_table_data():
    """验证表格中的实际数据"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN", "U3iYbe8cGaBrLEso6jMctMVgnVb")
    table_id = os.getenv("TABLE_ID", "tbl29O0osz3dn74L")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"🔍 验证飞书表格数据...")
    print(f"   APP_TOKEN: {app_token}")
    print(f"   TABLE_ID: {table_id}")
    print(f"   当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.INFO).build()
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()

    # 目标记录ID和股票名称映射
    target_records = {
        "rec25ORoaS06hp": "通富微电",
        "rec25ORoaS06yw": "英维克",
        "rec25ORoaS06IZ": "拓尔思",
        "rec25ORoaS06Sp": "两面针",
        "rec25ORoaS0714": "科大讯飞",
        "rec25ORoaS078B": "金山办公",
        "rec25ORoaS07fT": "中科曙光",
        "rec25ORoaS07ns": "科大国创"
    }

    print(f"\n📊 读取表格当前数据...")

    try:
        # 获取所有记录
        req = ListAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).build()
        resp = client.bitable.v1.app_table_record.list(req, option)

        if resp.success():
            records = resp.data.items if hasattr(resp.data, 'items') else []
            print(f"✅ 成功读取 {len(records)} 条记录")

            print(f"\n📋 目标股票当前价格:")
            found_records = 0

            for record in records:
                record_id = record.record_id
                if record_id in target_records:
                    found_records += 1
                    stock_name = target_records[record_id]

                    # 获取字段数据
                    fields = record.fields
                    current_price = fields.get("Current Price", "N/A")
                    name_field = fields.get("Name", fields.get("名称", "N/A"))

                    print(f"   {stock_name} ({record_id}): {current_price}")
                    print(f"     表格中名称: {name_field}")

            print(f"\n📈 统计: 找到 {found_records}/{len(target_records)} 个目标股票记录")

            if found_records < len(target_records):
                print(f"⚠️  部分记录未找到，可能是record_id不匹配")

        else:
            print(f"❌ 读取记录失败: {resp.code} - {resp.msg}")

    except Exception as e:
        print(f"❌ 验证过程异常: {e}")


def test_single_update():
    """测试单条记录更新"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN")
    table_id = os.getenv("TABLE_ID")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"\n🧪 测试单条记录更新...")

    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.INFO).build()
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()

    # 测试更新第一条记录（通富微电）
    test_record_id = "rec25ORoaS06hp"
    test_price = 999.99  # 明显的测试值

    print(f"   测试记录: {test_record_id}")
    print(f"   测试价格: {test_price}")

    try:
        # 单条更新
        records = [
            AppTableRecord.builder()
            .record_id(test_record_id)
            .fields({"Current Price": test_price})
            .build()
        ]

        req = BatchUpdateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(
                BatchUpdateAppTableRecordRequestBody.builder()
                .records(records)
                .build()
            ).build()

        resp = client.bitable.v1.app_table_record.batch_update(req, option)

        if resp.success():
            print(f"✅ 测试更新成功")

            # 等待几秒后验证
            print(f"   等待5秒后验证...")
            time.sleep(5)

            # 读取验证
            req = GetAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .record_id(test_record_id) \
                .build()

            resp = client.bitable.v1.app_table_record.get(req, option)

            if resp.success():
                current_price = resp.data.record.fields.get("Current Price", "N/A")
                print(f"   验证结果: Current Price = {current_price}")

                if current_price == test_price:
                    print(f"✅ 更新验证成功！表格已实际更新")
                else:
                    print(f"❌ 更新验证失败！表格显示: {current_price}，期望: {test_price}")
            else:
                print(f"❌ 验证读取失败: {resp.code} - {resp.msg}")

        else:
            print(f"❌ 测试更新失败: {resp.code} - {resp.msg}")

    except Exception as e:
        print(f"❌ 测试更新异常: {e}")


if __name__ == "__main__":
    verify_table_data()
    test_single_update()