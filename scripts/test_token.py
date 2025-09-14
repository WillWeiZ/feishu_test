#!/usr/bin/env python3
"""
测试token.py的简单脚本
不依赖Redis，直接测试基本功能
"""
import os
import sys
import time
from unittest.mock import Mock, patch

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feishu_token import FeishuUserTokenManager, load_env_file


def test_env_loading():
    """测试环境变量加载"""
    print("🔍 测试环境变量加载...")
    load_env_file("../.env")
    
    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")
    
    if app_id and app_secret:
        print(f"✅ 环境变量加载成功")
        print(f"   APP_ID: {app_id}")
        print(f"   APP_SECRET: {app_secret[:10]}...")
        return True
    else:
        print("❌ 环境变量加载失败")
        return False


def test_token_manager_init():
    """测试TokenManager初始化（模拟Redis）"""
    print("\n🔍 测试TokenManager初始化...")
    
    try:
        # 模拟Redis连接
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value = Mock()
            
            app_id = os.getenv("APP_ID", "test_app_id")
            app_secret = os.getenv("APP_SECRET", "test_app_secret")
            
            manager = FeishuUserTokenManager(app_id, app_secret)
            print("✅ TokenManager初始化成功")
            return True
    except Exception as e:
        print(f"❌ TokenManager初始化失败: {e}")
        return False


def test_key_generation():
    """测试Redis键名生成"""
    print("\n🔍 测试Redis键名生成...")
    
    try:
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value = Mock()
            
            manager = FeishuUserTokenManager("test_app", "test_secret")
            keys = manager._get_keys("test_user")
            
            expected_keys = ["access_token", "refresh_token", "expire_time", "lock"]
            for key in expected_keys:
                if key not in keys:
                    print(f"❌ 缺少键: {key}")
                    return False
            
            print("✅ 键名生成正确")
            for key, value in keys.items():
                print(f"   {key}: {value}")
            return True
    except Exception as e:
        print(f"❌ 键名生成测试失败: {e}")
        return False


def check_dependencies():
    """检查依赖项安装情况"""
    print("\n🔍 检查依赖项...")
    
    dependencies = [
        ("redis", "Redis客户端"),
        ("requests", "HTTP请求库"),
        ("time", "时间处理"),
    ]
    
    missing = []
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: {desc}")
        except ImportError:
            print(f"❌ {dep}: {desc} - 未安装")
            missing.append(dep)
    
    if missing:
        print(f"\n❌ 缺少依赖项: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依赖项已安装")
        return True


def check_redis_connection():
    """检查Redis连接"""
    print("\n🔍 检查Redis连接...")
    
    try:
        import redis
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        client.ping()
        print(f"✅ Redis连接成功 ({redis_host}:{redis_port})")
        return True
    except ImportError:
        print("❌ Redis模块未安装")
        return False
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("💡 请确保Redis服务正在运行")
        print(f"   在macOS上可以运行: brew services start redis")
        print(f"   在Docker中可以运行: docker run -d -p 6379:6379 redis")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试token.py...")
    print("=" * 50)
    
    tests = [
        ("环境变量加载", test_env_loading),
        ("依赖项检查", check_dependencies), 
        ("Redis连接", check_redis_connection),
        ("TokenManager初始化", test_token_manager_init),
        ("键名生成", test_key_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！token.py已准备好使用")
        print("💡 你可以运行: python scripts/token.py")
    else:
        print(f"\n⚠️  有 {len(results) - passed} 个测试失败")
        print("💡 请根据上述提示解决问题后再运行token.py")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)