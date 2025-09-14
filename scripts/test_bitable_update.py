#!/usr/bin/env python3
"""
直接测试多维表格更新权限
"""

import os
import json
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


def load_env_file(path: str = ".env") -> None:
    """加载环境变量文件"""
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


def test_bitable_permissions():
    """测试多维表格权限"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN", "U3iYbe8cGaBrLEso6jMctMVgnVb")
    table_id = os.getenv("TABLE_ID", "tbl29O0osz3dn74L")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"🔍 测试多维表格权限...")
    print(f"   APP_TOKEN: {app_token}")
    print(f"   TABLE_ID: {table_id}")
    print(f"   ACCESS_TOKEN: {access_token[:20]}...")

    # 创建client
    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()

    # 请求选项
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()

    # 测试1: 读取记录（应该成功）
    print(f"\n📖 测试1: 读取表格记录...")
    try:
        req = ListAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).build()
        resp = client.bitable.v1.app_table_record.list(req, option)

        if resp.success():
            records = resp.data.items if hasattr(resp.data, 'items') else []
            print(f"✅ 读取记录成功，共 {len(records)} 条记录")
        else:
            print(f"❌ 读取记录失败: {resp.code} - {resp.msg}")

    except Exception as e:
        print(f"❌ 读取记录异常: {e}")

    # 测试2: 更新单条记录（简化测试）
    print(f"\n✏️ 测试2: 更新单条记录...")

    # 使用第一个测试记录ID
    test_record_id = "rec25ORoaS06hp"
    test_value = 99.99

    try:
        # 构建单条更新请求
        record = AppTableRecord.builder().record_id(test_record_id).fields({"Current Price": test_value}).build()

        req = UpdateAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).record_id(test_record_id).request_body(
            UpdateAppTableRecordRequestBody.builder().fields({"Current Price": test_value}).build()
        ).build()

        resp = client.bitable.v1.app_table_record.update(req, option)

        if resp.success():
            print(f"✅ 更新记录成功: {test_record_id} -> {test_value}")
        else:
            print(f"❌ 更新记录失败: {resp.code} - {resp.msg}")
            print(f"   详细信息: {resp.raw.content}")

    except Exception as e:
        print(f"❌ 更新记录异常: {e}")

    # 测试3: 批量更新（原始方法）
    print(f"\n📝 测试3: 批量更新记录...")

    records = [
        AppTableRecord.builder().record_id("rec25ORoaS06hp").fields({"Current Price": 88.88}).build()
    ]

    try:
        req = BatchUpdateAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).request_body(
            BatchUpdateAppTableRecordRequestBody.builder().records(records).build()
        ).build()

        resp = client.bitable.v1.app_table_record.batch_update(req, option)

        if resp.success():
            print(f"✅ 批量更新成功")
        else:
            print(f"❌ 批量更新失败: {resp.code} - {resp.msg}")
            print(f"   详细信息: {resp.raw.content}")

    except Exception as e:
        print(f"❌ 批量更新异常: {e}")


if __name__ == "__main__":
    test_bitable_permissions()