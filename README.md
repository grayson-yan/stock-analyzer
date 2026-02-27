# 📈 股票综合分析工具

一个支持多维度股票分析的 Web 应用。

## 功能特性

- 📊 **K线图** - 交互式K线走势
- 📈 **技术面分析**
  - 均线系统 (MA5/10/20/60)
  - MACD 指标
  - RSI 相对强弱指标
  - 布林带通道
- 🀄 **缠论分析**
  - 分型识别（顶分型/底分型）
  - 笔的简化判断
  - 走势位置分析
- 📊 **韦科夫量价分析**
  - VWAP 趋势判断
  - 成交量异常检测
  - 弹簧测试信号
  - UTAD 信号识别
- 💰 **基本面分析**
  - 市盈率 (PE)
  - 市净率 (PB)
  - 市值、股息率
  - 52周高低点
- 🎯 **估值分析**
  - DCF 估值（简化版）
  - 相对估值（PE）
  - 52周价格位置

## 快速部署

### 方法一：Streamlit Cloud（推荐，免费）

1. 创建 GitHub 仓库，上传所有文件
2. 访问 [Streamlit Cloud](https://share.streamlit.io)
3. 链接你的 GitHub 仓库
4. 部署完成！

### 方法二：本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
streamlit run app.py
```

## 文件结构

```
stock-analyzer/
├── app.py              # 主应用
├── requirements.txt    # 依赖
└── README.md          # 说明
```

## 使用方法

1. 在左侧输入股票代码（如 AAPL、MSFT、TSLA）
2. 选择分析选项和时间周期
3. 查看综合分析结果
4. 参考综合建议

## 数据来源

- Yahoo Finance (yfinance)
- 实时更新

---
Made with ❤️
