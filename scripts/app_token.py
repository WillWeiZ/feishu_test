#!/usr/bin/env python3
"""
飞书App Access Token管理模块
用于获取和缓存应用级访问令牌，适合自动化任务场景
"""

import os
import time
import requests
import json
from typing import Optional, Tuple

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("警告: Redis不可用，将使用内存缓存")


class FeishuAppTokenManager:
    """飞书App Access Token管理器"""

    def __init__(self, app_id: str, app_secret: str, redis_host: str = "localhost", redis_port: int = 6379):
        self.app_id = app_id
        self.app_secret = app_secret
        self.buffer_time = 300  # 提前5分钟刷新

        # 初始化Redis客户端（如果可用）
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                # 测试连接
                self.redis_client.ping()
                print(f"✅ Redis连接成功 ({redis_host}:{redis_port})")
            except Exception as e:
                print(f"⚠️  Redis连接失败，使用内存缓存: {e}")
                self.redis_client = None

        # 内存缓存
        self._memory_cache = {}

    def get_app_access_token(self) -> str:
        """获取有效的App Access Token"""
        cache_key = f"feishu_app_access_token:{self.app_id}"

        # 尝试从缓存获取
        cached_token = self._get_from_cache(cache_key)
        if cached_token:
            token, expire_time = cached_token.split("|", 1)
            if int(time.time()) < (int(expire_time) - self.buffer_time):
                return token

        # 缓存失效，重新获取
        try:
            token, expires_in = self._fetch_app_access_token()
            expire_time = int(time.time()) + expires_in

            # 保存到缓存
            cache_value = f"{token}|{expire_time}"
            self._set_to_cache(cache_key, cache_value, expires_in)

            return token
        except Exception as e:
            raise Exception(f"获取App Access Token失败: {str(e)}")

    def _fetch_app_access_token(self) -> Tuple[str, int]:
        """从飞书API获取App Access Token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                app_access_token = result["app_access_token"]
                expires_in = result.get("expires_in", 7200)  # 默认2小时
                return app_access_token, expires_in
            else:
                raise Exception(f"API返回错误: {result.get('msg')} (错误码: {result.get('code')})")

        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应JSON解析失败: {str(e)}")

    def _get_from_cache(self, key: str) -> Optional[str]:
        """从缓存获取值"""
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception:
                pass

        # 使用内存缓存
        cache_data = self._memory_cache.get(key)
        if cache_data:
            value, expire_time = cache_data
            if time.time() < expire_time:
                return value
            else:
                # 过期，删除
                del self._memory_cache[key]

        return None

    def _set_to_cache(self, key: str, value: str, expire_seconds: int):
        """保存值到缓存"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, expire_seconds, value)
                return
            except Exception:
                pass

        # 使用内存缓存
        expire_time = time.time() + expire_seconds
        self._memory_cache[key] = (value, expire_time)

    def get_token_info(self) -> dict:
        """获取当前token信息（用于调试）"""
        cache_key = f"feishu_app_access_token:{self.app_id}"
        cached_token = self._get_from_cache(cache_key)

        if cached_token:
            token, expire_time = cached_token.split("|", 1)
            remaining_time = int(expire_time) - int(time.time())
            return {
                "token": f"{token[:10]}...",
                "expire_time": expire_time,
                "remaining_seconds": remaining_time,
                "is_valid": remaining_time > self.buffer_time
            }
        else:
            return {"status": "no_cache"}


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
                # 不覆盖已存在的环境变量
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"加载.env文件失败: {e}")


def get_app_token_from_env() -> Optional[str]:
    """从环境变量直接获取预设的App Access Token"""
    return os.getenv("APP_ACCESS_TOKEN")


# 使用示例和测试
if __name__ == "__main__":
    # 加载环境变量
    load_env_file()

    # 检查是否有预设的token
    preset_token = get_app_token_from_env()
    if preset_token:
        print(f"✅ 发现预设App Access Token: {preset_token[:10]}...")
        print("可以直接使用此token，无需动态获取")
        exit(0)

    # 从环境变量获取配置
    APP_ID = os.getenv("APP_ID")
    APP_SECRET = os.getenv("APP_SECRET")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    if not APP_ID or not APP_SECRET:
        print("错误: 请在.env文件中设置APP_ID和APP_SECRET")
        print("或者直接设置APP_ACCESS_TOKEN使用预设token")
        exit(1)

    print(f"使用配置: APP_ID={APP_ID}, REDIS_HOST={REDIS_HOST}:{REDIS_PORT}")

    # 创建token管理器并测试
    token_manager = FeishuAppTokenManager(APP_ID, APP_SECRET, REDIS_HOST, REDIS_PORT)

    try:
        # 获取token
        access_token = token_manager.get_app_access_token()
        print(f"✅ App Access Token获取成功: {access_token[:20]}...")

        # 显示token信息
        info = token_manager.get_token_info()
        print(f"Token信息: {info}")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print("\n💡 提示:")
        print("1. 确保APP_ID和APP_SECRET正确")
        print("2. 检查网络连接")
        print("3. 或者在.env中设置APP_ACCESS_TOKEN使用预设token")