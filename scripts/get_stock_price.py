import akshare as ak
import datetime
import pandas as pd

# 目标股票映射：股票名称 -> 股票代码
target_stocks = {
    "通富微电": "002156",
    "英维克": "002837",
    "拓尔思": "300229",
    "两面针": "600249",
    "科大讯飞": "002230",
    "金山办公": "688111",
    "中科曙光": "603019",
    "科大国创": "300520"
}

def get_stock_prices():
    """获取目标股票的前一天收盘价"""
    # 获取前一天日期
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y%m%d")

    print(f"获取 {date_str} 的股票价格数据...")

    all_data = []

    for stock_name, stock_code in target_stocks.items():
        try:
            print(f"正在获取 {stock_name} ({stock_code}) 的价格...")

            # 获取股票历史数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=date_str,
                end_date=date_str,
                adjust=""
            )

            if not df.empty:
                # 添加股票名称列
                df['股票名称'] = stock_name
                df['股票代码'] = stock_code
                all_data.append(df)
                print(f"  ✅ {stock_name}: {df.iloc[0]['收盘']}")
            else:
                print(f"  ❌ {stock_name}: 无数据")

        except Exception as e:
            print(f"  ❌ {stock_name}: 获取失败 - {e}")

    if all_data:
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)

        # 保存到CSV文件
        output_path = "data/'all_stock.csv"
        combined_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n✅ 数据已保存到 {output_path}")
        print(f"共获取 {len(combined_df)} 条记录")

        return combined_df
    else:
        print("\n❌ 未获取到任何股票数据")
        return None

if __name__ == "__main__":
    get_stock_prices()