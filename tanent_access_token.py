import json
import os

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


# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
def main():
    # 加载环境变量
    load_env_file()

    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")

    print(f"使用APP_ID: {app_id}")
    print(f"使用APP_SECRET: {app_secret[:10]}...{app_secret[-4:]}")

    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: InternalTenantAccessTokenRequest = InternalTenantAccessTokenRequest.builder() \
        .request_body(InternalTenantAccessTokenRequestBody.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .build()) \
        .build()

    # 发起请求
    response: InternalTenantAccessTokenResponse = client.auth.v3.tenant_access_token.internal(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.auth.v3.tenant_access_token.internal failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    print("✅ 成功获取Tenant Access Token!")

    # 提取token
    try:
        response_data = json.loads(response.raw.content)
        tenant_access_token = response_data.get("tenant_access_token")
        expires_in = response_data.get("expires_in", 7200)

        print(f"Token: {tenant_access_token}")
        print(f"有效期: {expires_in}秒 ({expires_in//3600}小时)")

        # 更新.env文件
        update_env_token(tenant_access_token)

    except Exception as e:
        print(f"解析响应失败: {e}")
        print(f"原始响应: {response.raw.content}")


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

        print(f"✅ Token已更新到.env文件")

    except Exception as e:
        print(f"❌ 更新.env文件失败: {e}")
        print(f"请手动将以下内容添加到.env:")
        print(f'APP_ACCESS_TOKEN="{token}"')


if __name__ == "__main__":
    main()
