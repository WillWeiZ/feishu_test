#!/usr/bin/env python3
"""
直接测试飞书应用凭证和获取App Access Token
"""

import os
import requests
import json


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


def test_get_app_access_token(app_id: str, app_secret: str) -> None:
    """测试获取App Access Token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    print(f"🔍 测试获取App Access Token...")
    print(f"   APP_ID: {app_id}")
    print(f"   APP_SECRET: {app_secret[:10]}...{app_secret[-4:]}")
    print(f"   请求URL: {url}")
    print(f"   请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"\n📡 响应状态码: {response.status_code}")
        print(f"📡 响应头: {dict(response.headers)}")

        try:
            result = response.json()
            print(f"📡 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if result.get("code") == 0:
                app_access_token = result["app_access_token"]
                expires_in = result.get("expires_in", 7200)
                print(f"\n✅ 成功获取App Access Token!")
                print(f"   Token: {app_access_token}")
                print(f"   有效期: {expires_in}秒 ({expires_in//3600}小时)")

                # 保存到环境变量文件
                save_token_to_env(app_access_token)
                return app_access_token

            else:
                print(f"\n❌ API返回错误:")
                print(f"   错误码: {result.get('code')}")
                print(f"   错误信息: {result.get('msg')}")
                return None

        except json.JSONDecodeError as e:
            print(f"❌ 响应JSON解析失败: {e}")
            print(f"原始响应内容: {response.text}")
            return None

    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None


def save_token_to_env(token: str) -> None:
    """将新token保存到.env文件"""
    env_path = ".env"
    if not os.path.exists(env_path):
        print("⚠️  .env文件不存在，无法保存token")
        return

    try:
        # 读取现有内容
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 更新或添加APP_ACCESS_TOKEN
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("APP_ACCESS_TOKEN") or line.strip().startswith("# APP_ACCESS_TOKEN"):
                lines[i] = f'APP_ACCESS_TOKEN="{token}"\n'
                updated = True
                break

        if not updated:
            lines.append(f'APP_ACCESS_TOKEN="{token}"\n')

        # 写回文件
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ 新token已保存到.env文件")

    except Exception as e:
        print(f"❌ 保存token到.env失败: {e}")
        print(f"请手动将以下内容添加到.env文件:")
        print(f'APP_ACCESS_TOKEN="{token}"')


def main():
    # 加载环境变量
    load_env_file()

    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")

    print("🚀 飞书应用凭证测试")
    print("=" * 50)

    if not app_id:
        print("❌ 错误: 未找到APP_ID，请检查.env文件")
        return False

    if not app_secret:
        print("❌ 错误: 未找到APP_SECRET，请检查.env文件")
        return False

    # 测试获取token
    token = test_get_app_access_token(app_id, app_secret)

    if token:
        print("\n🎉 测试成功！")
        print("现在可以运行: python scripts/update_all.py")
        return True
    else:
        print("\n❌ 测试失败，请检查应用凭证")
        return False


if __name__ == "__main__":
    success = main()