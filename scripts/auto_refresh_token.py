#!/usr/bin/env python3
"""
自动刷新飞书Token并执行股票价格更新
当token过期时自动获取新token并更新.env文件
"""

import os
import sys
import subprocess
import json
import lark_oapi as lark
from lark_oapi.api.auth.v3 import *


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


def get_new_token() -> str:
    """获取新的tenant access token"""
    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")

    if not app_id or not app_secret:
        raise ValueError("APP_ID或APP_SECRET未配置")

    print(f"🔄 正在获取新的Token (APP_ID: {app_id[:8]}...)")

    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.ERROR) \
        .build()

    # 构造请求对象
    request = InternalTenantAccessTokenRequest.builder() \
        .request_body(InternalTenantAccessTokenRequestBody.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .build()) \
        .build()

    # 发起请求
    response = client.auth.v3.tenant_access_token.internal(request)

    if not response.success():
        raise Exception(f"获取Token失败: {response.code} - {response.msg}")

    # 提取token
    response_data = json.loads(response.raw.content)
    tenant_access_token = response_data.get("tenant_access_token")
    expires_in = response_data.get("expires_in", 7200)

    print(f"✅ 成功获取Token: {tenant_access_token[:20]}...")
    print(f"📅 有效期: {expires_in}秒 ({expires_in//3600}小时)")

    return tenant_access_token


def update_env_token(token: str) -> None:
    """更新.env文件中的token"""
    env_path = ".env"
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 更新APP_ACCESS_TOKEN
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("APP_ACCESS_TOKEN") or line.strip().startswith("# APP_ACCESS_TOKEN"):
                lines[i] = f'APP_ACCESS_TOKEN="{token}"\n'
                updated = True
                break

        if not updated:
            lines.append(f'APP_ACCESS_TOKEN="{token}"\n')

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"💾 Token已更新到.env文件")

    except Exception as e:
        print(f"❌ 更新.env文件失败: {e}")
        raise


def run_update() -> bool:
    """运行股票价格更新，返回是否成功"""
    try:
        print("\n🔄 开始执行股票价格更新...")

        # 运行主程序
        result = subprocess.run([sys.executable, "scripts/main.py"],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 股票价格更新成功")
            return True
        else:
            print(f"❌ 股票价格更新失败")
            if "99991663" in result.stderr or "99991677" in result.stderr:
                print("🔍 检测到Token过期错误")
                return False
            else:
                print(f"错误输出: {result.stderr}")
                return False

    except Exception as e:
        print(f"❌ 执行更新时出错: {e}")
        return False


def main():
    """主函数：自动获取token并执行更新"""
    print("🚀 启动自动Token刷新和股票价格更新...")

    # 加载环境变量
    load_env_file()

    # 首次尝试运行更新
    success = run_update()

    # 如果失败，尝试刷新token再运行
    if not success:
        try:
            print("\n🔄 尝试刷新Token...")
            new_token = get_new_token()
            update_env_token(new_token)

            # 重新加载环境变量
            os.environ.pop("APP_ACCESS_TOKEN", None)  # 清除旧的
            load_env_file()

            print("\n🔄 使用新Token重新执行更新...")
            success = run_update()

            if success:
                print("\n🎉 Token刷新并更新成功！")
            else:
                print("\n❌ Token刷新后仍然失败，请检查配置")
                sys.exit(1)

        except Exception as e:
            print(f"\n❌ 刷新Token失败: {e}")
            sys.exit(1)
    else:
        print("\n🎉 更新成功，无需刷新Token")


if __name__ == "__main__":
    main()