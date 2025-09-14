#!/usr/bin/env python3
"""
检查应用权限和多维表格访问权限
"""

import os
import json
import requests
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


def check_app_info():
    """检查应用信息"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"🔍 检查应用权限...")
    print(f"   APP_TOKEN: {app_token}")
    print(f"   ACCESS_TOKEN: {access_token[:20]}...")

    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()

    # 检查应用信息
    try:
        req = GetAppRequest.builder().app_token(app_token).build()
        resp = client.bitable.v1.app.get(req, option)

        if resp.success():
            print(f"✅ 应用信息获取成功")
            app_data = json.loads(resp.raw.content)
            print(f"   应用数据: {json.dumps(app_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 应用信息获取失败: {resp.code} - {resp.msg}")

    except Exception as e:
        print(f"❌ 检查应用信息异常: {e}")


def check_table_permissions():
    """检查表格权限"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN")
    table_id = os.getenv("TABLE_ID")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"\n🔍 检查表格权限...")

    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()

    # 尝试不同的API调用来确定权限范围
    apis_to_test = [
        ("获取表格信息", lambda: client.bitable.v1.app_table.get(
            GetAppTableRequest.builder().app_token(app_token).table_id(table_id).build(), option)),

        ("获取字段列表", lambda: client.bitable.v1.app_table_field.list(
            ListAppTableFieldRequest.builder().app_token(app_token).table_id(table_id).build(), option)),

        ("获取记录列表", lambda: client.bitable.v1.app_table_record.list(
            ListAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).build(), option)),
    ]

    for api_name, api_call in apis_to_test:
        try:
            print(f"\n📋 测试: {api_name}")
            resp = api_call()
            if resp.success():
                print(f"✅ {api_name}成功")
            else:
                print(f"❌ {api_name}失败: {resp.code} - {resp.msg}")
        except Exception as e:
            print(f"❌ {api_name}异常: {e}")


def test_direct_api_call():
    """直接使用requests测试API调用"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN")
    table_id = os.getenv("TABLE_ID")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print(f"\n🔍 直接API测试...")

    # 测试批量更新API
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 简单的测试数据
    data = {
        "records": [
            {
                "record_id": "rec25ORoaS06hp",
                "fields": {
                    "Current Price": 99.99
                }
            }
        ]
    }

    print(f"   URL: {url}")
    print(f"   Headers: {headers}")
    print(f"   Data: {json.dumps(data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"\n📡 响应状态码: {response.status_code}")

        try:
            result = response.json()
            print(f"📡 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print(f"📡 响应内容 (原始): {response.text}")

    except Exception as e:
        print(f"❌ 直接API调用异常: {e}")


if __name__ == "__main__":
    check_app_info()
    check_table_permissions()
    test_direct_api_call()