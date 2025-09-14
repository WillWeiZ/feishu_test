#!/usr/bin/env python3
"""
调试权限问题 - 尝试不同的API调用方法
"""

import os
import json
import requests


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


def test_different_update_methods():
    """测试不同的更新方法"""
    load_env_file()

    app_token = os.getenv("APP_TOKEN")
    table_id = os.getenv("TABLE_ID")
    access_token = os.getenv("APP_ACCESS_TOKEN")

    print("🔧 尝试不同的更新方法...")

    # 方法1: 使用user_id_type参数
    print("\n📝 方法1: 批量更新 (user_id_type=user_id)")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

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

    # 添加user_id_type参数
    params = {"user_id_type": "user_id"}

    try:
        response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   异常: {e}")

    # 方法2: 单条记录更新
    print("\n📝 方法2: 单条记录更新")
    record_id = "rec25ORoaS06hp"
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"

    data = {
        "fields": {
            "Current Price": 88.88
        }
    }

    try:
        response = requests.put(url, headers=headers, json=data, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   异常: {e}")

    # 方法3: 不同的字段名尝试
    print("\n📝 方法3: 尝试不同字段名")

    # 先获取字段信息
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    try:
        response = requests.get(fields_url, headers=headers, timeout=10)
        if response.status_code == 200:
            fields_data = response.json()
            print(f"   可用字段:")
            items = fields_data.get('data', {}).get('items', [])
            for field in items:
                print(f"     - {field.get('field_name')} ({field.get('field_id')})")

            # 尝试使用字段ID而不是字段名
            if items:
                target_field = None
                for field in items:
                    if 'price' in field.get('field_name', '').lower() or 'current' in field.get('field_name', '').lower():
                        target_field = field
                        break

                if target_field:
                    field_id = target_field.get('field_id')
                    field_name = target_field.get('field_name')

                    print(f"   尝试更新字段: {field_name} ({field_id})")

                    # 使用字段ID
                    data = {
                        "records": [
                            {
                                "record_id": "rec25ORoaS06hp",
                                "fields": {
                                    field_id: 77.77
                                }
                            }
                        ]
                    }

                    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    print(f"   使用字段ID - 状态码: {response.status_code}")
                    print(f"   使用字段ID - 响应: {response.json()}")

    except Exception as e:
        print(f"   获取字段信息异常: {e}")


def check_app_installation():
    """检查应用是否需要安装到多维表格"""
    print("\n🔍 权限问题可能的原因:")
    print("1. 应用可能需要被明确安装到多维表格中")
    print("2. 多维表格的协作设置可能限制了应用访问")
    print("3. 可能需要多维表格管理员授予特定权限")
    print("4. 应用权限可能需要用户级授权而不是应用级授权")

    print("\n💡 建议解决步骤:")
    print("1. 在多维表格中检查 '协作' 或 '设置' 选项")
    print("2. 查看是否有 '应用' 或 '插件' 管理选项")
    print("3. 确认应用是否需要用户主动授权")
    print("4. 检查多维表格的编辑权限设置")


if __name__ == "__main__":
    test_different_update_methods()
    check_app_installation()