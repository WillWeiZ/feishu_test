import time
import redis
import requests

class FeishuUserTokenManager:
    def __init__(self, app_id, app_secret, redis_host="localhost", redis_port=6379):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.buffer_time = 300  # 提前5分钟刷新，避免过期
        
    def _get_keys(self, user_id):
        """获取用户相关的Redis键名"""
        return {
            "access_token": f"feishu_user_access_token:{user_id}",
            "refresh_token": f"feishu_user_refresh_token:{user_id}",
            "expire_time": f"feishu_user_token_expire:{user_id}",
            "lock": f"feishu_user_token_lock:{user_id}"
        }
    
    def get_user_access_token(self, user_id):
        """获取指定用户的有效Access Token"""
        keys = self._get_keys(user_id)
        
        # 尝试从缓存获取
        access_token = self.redis_client.get(keys["access_token"])
        refresh_token = self.redis_client.get(keys["refresh_token"])
        expire_time = self.redis_client.get(keys["expire_time"])
        
        # 检查Token是否有效
        if access_token and refresh_token and expire_time:
            if int(time.time()) < (int(expire_time) - self.buffer_time):
                return access_token
        
        # Token无效，需要刷新
        with self._redis_lock(keys["lock"], timeout=10):
            # 双重检查，避免并发问题
            access_token = self.redis_client.get(keys["access_token"])
            refresh_token = self.redis_client.get(keys["refresh_token"])
            expire_time = self.redis_client.get(keys["expire_time"])
            
            if access_token and refresh_token and expire_time:
                if int(time.time()) < (int(expire_time) - self.buffer_time):
                    return access_token
            
            # 尝试刷新Token
            if refresh_token:
                try:
                    new_access_token, new_refresh_token, new_expire = self._refresh_user_token(refresh_token)
                    self.redis_client.set(keys["access_token"], new_access_token)
                    self.redis_client.set(keys["refresh_token"], new_refresh_token)
                    self.redis_client.set(keys["expire_time"], new_expire)
                    return new_access_token
                except Exception as e:
                    print(f"刷新Token失败: {str(e)}")
            
            # 如果刷新失败，可能需要重新授权
            raise Exception(f"用户 {user_id} 的Token已过期且无法刷新，请重新授权")
    
    def save_initial_tokens(self, user_id, access_token, refresh_token, expires_in):
        """保存初始获取的Tokens（从授权流程获得）"""
        keys = self._get_keys(user_id)
        expire_time = int(time.time()) + expires_in
        self.redis_client.set(keys["access_token"], access_token)
        self.redis_client.set(keys["refresh_token"], refresh_token)
        self.redis_client.set(keys["expire_time"], expire_time)
    
    def _refresh_user_token(self, refresh_token):
        """使用Refresh Token获取新的Access Token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/user_access_token/refresh"
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "refresh_token",
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "refresh_token": refresh_token
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                access_token = result["access_token"]
                new_refresh_token = result["refresh_token"]
                expires_in = result["expires_in"]
                expire_time = int(time.time()) + expires_in
                return access_token, new_refresh_token, expire_time
            else:
                raise Exception(f"刷新Token失败: {result.get('msg')} (错误码: {result.get('code')})")
        except Exception as e:
            raise Exception(f"调用刷新接口失败: {str(e)}")
    
    def _redis_lock(self, lock_key, timeout=10):
        """Redis分布式锁，避免并发刷新"""
        return RedisLock(self.redis_client, lock_key, timeout)


class RedisLock:
    """简单的Redis分布式锁实现"""
    def __init__(self, redis_client, lock_key, timeout):
        self.redis_client = redis_client
        self.lock_key = lock_key
        self.timeout = timeout
        self.locked = False

    def __enter__(self):
        # 尝试获取锁，设置过期时间避免死锁
        self.locked = self.redis_client.set(
            self.lock_key, "1", ex=self.timeout, nx=True
        )
        return self.locked

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.locked:
            self.redis_client.delete(self.lock_key)
        return False


def load_env_file(path: str = ".env") -> None:
    """简单的.env文件加载器"""
    import os
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
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


# 使用示例
if __name__ == "__main__":
    import os
    
    # 加载环境变量
    load_env_file()
    
    # 从环境变量获取配置
    APP_ID = os.getenv("APP_ID")
    APP_SECRET = os.getenv("APP_SECRET") 
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    USER_ID = os.getenv("USER_ID", "default_user")
    
    if not APP_ID or not APP_SECRET:
        print("错误: 请在.env文件中设置APP_ID和APP_SECRET")
        exit(1)
    
    print(f"使用配置: APP_ID={APP_ID}, REDIS_HOST={REDIS_HOST}:{REDIS_PORT}, USER_ID={USER_ID}")
    
    token_manager = FeishuUserTokenManager(APP_ID, APP_SECRET, REDIS_HOST, REDIS_PORT)
    
    try:
        # 检查是否有初始tokens需要保存
        initial_access_token = os.getenv("USER_ACCESS_TOKEN")
        initial_refresh_token = os.getenv("USER_REFRESH_TOKEN")
        
        if initial_access_token and initial_refresh_token:
            print("发现初始tokens，正在保存...")
            token_manager.save_initial_tokens(USER_ID, initial_access_token, initial_refresh_token, 7200)
            print("初始tokens已保存")
        
        # 获取有效token
        access_token = token_manager.get_user_access_token(USER_ID)
        print(f"✅ 有效User Access Token: {access_token}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print("\n💡 提示:")
        print("1. 确保Redis服务正在运行")
        print("2. 如果是首次使用，需要先完成飞书授权流程获取initial tokens")
        print("3. 可以在.env文件中设置USER_ACCESS_TOKEN和USER_REFRESH_TOKEN进行测试")
