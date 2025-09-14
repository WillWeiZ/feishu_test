# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个飞书多维表格自动更新工具，通过 AkShare 获取股票实时价格并更新到飞书多维表格中。项目使用 Python 开发，集成了股票数据获取和飞书 API 调用功能。

## 环境设置

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（创建 `.env` 文件）：
   ```
   # 基本配置
   APP_TOKEN=你的飞书应用token
   TABLE_ID=你的表格ID
   TARGET_FIELD_ID=目标字段ID（可选）
   TARGET_FIELD_NAME=目标字段名称（默认：Current Price）

   # Token配置（推荐使用App Access Token）
   APP_ACCESS_TOKEN=你的应用访问令牌（推荐）

   # 或者使用动态获取方式
   APP_ID=你的应用ID
   APP_SECRET=你的应用密钥

   # Redis配置（可选，用于token缓存）
   REDIS_HOST=localhost
   REDIS_PORT=6379

   # User Token（备用方案，会2小时过期）
   USER_ACCESS_TOKEN=你的用户访问token（不推荐）
   ```

## 核心命令

### 运行完整更新流程
```bash
python scripts/main.py
```
这个命令会依次执行：
1. 获取股票价格数据
2. 更新飞书多维表格

### 单独获取股票数据
```bash
python scripts/get_stock_price.py  
```

### 单独更新飞书表格
```bash
python scripts/update_all.py
```

### 测试App Token功能
```bash
python scripts/app_token.py
```

### 测试User Token管理（如果使用）
```bash
python scripts/feishu_token.py  # 重命名后的token.py
python scripts/test_token.py
```

## 项目架构

### 主要脚本
- `scripts/main.py` - 主入口脚本，协调整个数据流程
- `scripts/get_stock_price.py` - 使用 AkShare 获取A股实时数据
- `scripts/update_all.py` - 飞书多维表格更新逻辑，支持App Token和User Token
- `scripts/app_token.py` - App Access Token管理器，支持动态获取和缓存
- `scripts/feishu_token.py` - User Access Token管理器，支持自动刷新（备用）
- `scripts/test_token.py` - User Token功能测试脚本

### 数据流程
1. `get_stock_price.py` 通过 AkShare 获取A股现货数据
2. 数据保存到 `data/'all_stock.csv` （注意文件名包含单引号）
3. `update_all.py` 读取CSV文件，提取目标股票价格
4. 通过飞书 API 批量更新多维表格中的特定记录

### 目标股票列表
项目硬编码了8只目标股票的记录ID映射：
- 通富微电 (rec25ORoaS06hp)
- 英维克 (rec25ORoaS06yw)  
- 拓尔思 (rec25ORoaS06IZ)
- 两面针 (rec25ORoaS06Sp)
- 科大讯飞 (rec25ORoaS0714)
- 金山办公 (rec25ORoaS078B)
- 中科曙光 (rec25ORoaS07fT)
- 科大国创 (rec25ORoaS07ns)

### 飞书API集成
- 使用 `lark-oapi` SDK 进行飞书API调用
- **Token策略**：优先使用App Access Token，自动回退到User Access Token
- 支持字段ID和字段名称两种更新方式
- 包含错误处理和日志记录
- 使用批量更新接口提高效率
- 支持Redis缓存（可选）和内存缓存

### Token类型对比

| 特性 | App Access Token | User Access Token |
|------|------------------|-------------------|
| **有效期** | 通常24小时+ | 2小时 |
| **刷新方式** | 应用凭证自动获取 | 需要refresh_token |
| **权限范围** | 应用级权限 | 用户级权限 |
| **适用场景** | 自动化任务（推荐） | 需要用户身份的操作 |
| **维护成本** | 低 | 高（需要定期刷新） |

## GitHub Actions 自动化

项目配置了 GitHub Actions 工作流 `.github/workflows/update-feishu.yml`：

### 运行时间表
- **股价更新时间**：工作日（周一到周五）北京时间
  - 12:00 (中午休市时间)
  - 15:30 (收盘后)
- **手动触发**：支持通过 GitHub Actions 界面手动运行

### GitHub Secrets 配置

需要在 GitHub Secrets 中配置以下变量：

#### 基本配置
- `FEISHU_APP_TOKEN` - 飞书多维表格应用token
- `FEISHU_TABLE_ID` - 目标表格ID

#### App Token配置（推荐）
- `FEISHU_APP_ID` - 飞书应用ID
- `FEISHU_APP_SECRET` - 飞书应用密钥

#### 可选配置
- `FEISHU_TARGET_FIELD_ID` - 目标字段ID（可选）
- `FEISHU_TARGET_FIELD_NAME` - 目标字段名称（可选）
- `FEISHU_USER_ACCESS_TOKEN` - 用户访问token（备用）

### 功能特性
- **智能token管理**：优先使用App Access Token，自动回退到User Token
- **错误处理**：包含完整的错误日志和失败时的文件上传
- **时区正确性**：使用Asia/Shanghai时区确保准确的交易时间

## 权限配置和故障排除

### 飞书应用权限要求

使用App Access Token需要在飞书开发者控制台配置以下权限：

1. **多维表格权限**：
   - `bitable:app` - 查看应用
   - `bitable:app:readonly` - 只读访问应用信息
   - `bitable:app:write` - **写入应用数据（必需）**

2. **字段权限**：
   - `bitable:field` - 管理字段
   - `bitable:field:readonly` - 只读访问字段

3. **记录权限**：
   - `bitable:record` - 管理记录
   - `bitable:record:write` - **写入记录数据（必需）**

### 常见错误和解决方案

| 错误代码 | 错误信息 | 原因 | 解决方案 |
|---------|----------|------|----------|
| 91403 | Forbidden | 应用权限不足 | 在飞书开发者控制台添加写入权限 |
| 99991677 | Authentication token expired | User Token过期 | 使用App Token或刷新User Token |
| 10003 | invalid param | APP_ID/APP_SECRET错误 | 检查应用凭证配置 |

### 权限检查命令
```bash
# 测试token有效性和权限
python scripts/app_token.py

# 测试完整更新流程
python scripts/update_all.py
```

## 开发注意事项

1. **数据文件路径**：CSV文件名为 `data/'all_stock.csv`，包含单引号
2. **环境变量优先**：脚本优先读取环境变量配置，其次使用代码中的默认值
3. **错误处理**：所有API调用都包含完整的错误处理和日志输出
4. **字段映射**：支持通过字段ID或字段名称进行数据更新
5. **Python版本**：项目使用Python 3.10+
6. **时区设置**：GitHub Actions 使用 Asia/Shanghai 时区
7. **模块冲突**：避免文件名与Python内置模块冲突（如`token.py`已重命名为`feishu_token.py`）