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
   APP_TOKEN=你的飞书应用token
   TABLE_ID=你的表格ID  
   USER_ACCESS_TOKEN=你的用户访问token
   TARGET_FIELD_ID=目标字段ID（可选）
   TARGET_FIELD_NAME=目标字段名称（默认：Current Price）
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

## 项目架构

### 主要脚本
- `scripts/main.py` - 主入口脚本，协调整个数据流程
- `scripts/get_stock_price.py` - 使用 AkShare 获取A股实时数据
- `scripts/update_all.py` - 飞书多维表格更新逻辑，包含数据映射和API调用

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
- 支持字段ID和字段名称两种更新方式
- 包含错误处理和日志记录
- 使用批量更新接口提高效率

## 开发注意事项

1. **数据文件路径**：CSV文件名为 `data/'all_stock.csv`，包含单引号
2. **环境变量优先**：脚本优先读取环境变量配置，其次使用代码中的默认值
3. **错误处理**：所有API调用都包含完整的错误处理和日志输出
4. **字段映射**：支持通过字段ID或字段名称进行数据更新