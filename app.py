"""
股票分析工具 Pro Max - V3.1
支持美股、A股、港股模糊搜索
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from fuzzywuzzy import fuzz
import json

# 页面配置
st.set_page_config(
    page_title="股票分析工具 Pro Max",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS美化
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        font-size: 42px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #1f77b4, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px 0;
        margin-bottom: 10px;
    }
    
    /* 副标题 */
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 14px;
        margin-bottom: 30px;
    }
    
    /* 搜索框样式 */
    .search-box {
        background: #1e1e1e;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
    }
    
    /* 卡片样式 */
    .stock-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        border: 1px solid #333;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: #262730;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    /* 信号标签 */
    .signal-buy {
        background: #00c853;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    .signal-sell {
        background: #ff1744;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    .signal-watch {
        background: #ffab00;
        color: black;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    /* 分隔线 */
    hr {
        margin: 30px 0;
    }
    
    /* 侧边栏 */
    .css-1d391kg {
        background: #1e1e1e;
    }
</style>
""", unsafe_allow_html=True)

# 股票数据库（用于模糊搜索）
STOCK_DATABASE = {
    # 美股
    "MSFT": {"name": "Microsoft Corporation", "market": "US", "full_code": "MSFT"},
    "AAPL": {"name": "Apple Inc", "market": "US", "full_code": "AAPL"},
    "GOOGL": {"name": "Alphabet Inc", "market": "US", "full_code": "GOOGL"},
    "GOOG": {"name": "Alphabet Inc Class C", "market": "US", "full_code": "GOOG"},
    "AMZN": {"name": "Amazon.com Inc", "market": "US", "full_code": "AMZN"},
    "META": {"name": "Meta Platforms Inc", "market": "US", "full_code": "META"},
    "TSLA": {"name": "Tesla Inc", "market": "US", "full_code": "TSLA"},
    "NVDA": {"name": "NVIDIA Corporation", "market": "US", "full_code": "NVDA"},
    "AMD": {"name": "Advanced Micro Devices", "market": "US", "full_code": "AMD"},
    "INTC": {"name": "Intel Corporation", "market": "US", "full_code": "INTC"},
    "NFLX": {"name": "Netflix Inc", "market": "US", "full_code": "NFLX"},
    "DIS": {"name": "Walt Disney Co", "market": "US", "full_code": "DIS"},
    "JPM": {"name": "JPMorgan Chase & Co", "market": "US", "full_code": "JPM"},
    "V": {"name": "Visa Inc", "market": "US", "full_code": "V"},
    "JNJ": {"name": "Johnson & Johnson", "market": "US", "full_code": "JNJ"},
    "WMT": {"name": "Walmart Inc", "market": "US", "full_code": "WMT"},
    "PG": {"name": "Procter & Gamble", "market": "US", "full_code": "PG"},
    "MA": {"name": "Mastercard Inc", "market": "US", "full_code": "MA"},
    "HD": {"name": "Home Depot Inc", "market": "US", "full_code": "HD"},
    "BAC": {"name": "Bank of America", "market": "US", "full_code": "BAC"},
    
    # A股（沪市+深市）
    "600060": {"name": "海信视像", "market": "A", "full_code": "600060.SS"},
    "600785": {"name": "新华百货", "market": "A", "full_code": "600785.SS"},
    "603986": {"name": "兆易创新", "market": "A", "full_code": "603986.SS"},
    "002050": {"name": "三花智控", "market": "A", "full_code": "002050.SZ"},
    "688521": {"name": "芯原股份", "market": "A", "full_code": "688521.SS"},
    "000001": {"name": "平安银行", "market": "A", "full_code": "000001.SZ"},
    "600519": {"name": "贵州茅台", "market": "A", "full_code": "600519.SS"},
    "600036": {"name": "招商银行", "market": "A", "full_code": "600036.SS"},
    "601318": {"name": "中国平安", "market": "A", "full_code": "601318.SS"},
    "000858": {"name": "五粮液", "market": "A", "full_code": "000858.SZ"},
    "002594": {"name": "比亚迪", "market": "A", "full_code": "002594.SZ"},
    "300750": {"name": "宁德时代", "market": "A", "full_code": "300750.SZ"},
    "601888": {"name": "中国中免", "market": "A", "full_code": "601888.SS"},
    "600276": {"name": "恒瑞医药", "market": "A", "full_code": "600276.SS"},
    "000333": {"name": "美的集团", "market": "A", "full_code": "000333.SZ"},
    
    # 港股
    "9988": {"name": "阿里巴巴-SW", "market": "HK", "full_code": "9988.HK"},
    "0700": {"name": "腾讯控股", "market": "HK", "full_code": "0700.HK"},
    "3690": {"name": "美团-W", "market": "HK", "full_code": "3690.HK"},
    "1810": {"name": "小米集团-W", "market": "HK", "full_code": "1810.HK"},
    "9618": {"name": "京东集团-SW", "market": "HK", "full_code": "9618.HK"},
    "9888": {"name": "百度集团-SW", "market": "HK", "full_code": "9888.HK"},
    "1024": {"name": "快手-W", "market": "HK", "full_code": "1024.HK"},
    "2388": {"name": "港交所", "market": "HK", "full_code": "2388.HK"},
    "0939": {"name": "建设银行-H", "market": "HK", "full_code": "0939.HK"},
    "1398": {"name": "工商银行-H", "market": "HK", "full_code": "1398.HK"},
}

def fuzzy_search(query, limit=5):
    """模糊搜索股票"""
    if not query:
        return []
    
    query = query.upper().strip()
    results = []
    
    for code, info in STOCK_DATABASE.items():
        # 计算匹配度
        name_score = fuzz.ratio(query.lower(), info["name"].lower())
        code_score = fuzz.ratio(query, code)
        partial_code = fuzz.partial_ratio(query, code)
        
        # 综合得分
        max_score = max(name_score, code_score, partial_code)
        
        if max_score > 50:
            results.append({
                "code": code,
                "name": info["name"],
                "market": info["market"],
                "full_code": info["full_code"],
                "score": max_score
            })
    
    # 按得分排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def get_stock_code(user_input):
    """将用户输入转换为标准股票代码"""
    user_input = user_input.strip().upper()
    
    # 如果直接匹配
    if user_input in STOCK_DATABASE:
        return STOCK_DATABASE[user_input]["full_code"]
    
    # 模糊搜索
    results = fuzzy_search(user_input, 1)
    if results:
        return results[0]["full_code"]
    
    # 尝试识别市场
    # A股：6位数字
    if user_input.isdigit() and len(user_input) == 6:
        if user_input.startswith("6"):
            return f"{user_input}.SS"
        else:
            return f"{user_input}.SZ"
    
    # 港股：4位数字
    if user_input.isdigit() and len(user_input) == 4:
        return f"{user_input}.HK"
    
    return None

@st.cache_data(ttl=300)
def get_stock_data(symbol, period="1y"):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        info = {}
        try:
            info = ticker.info or {}
        except:
            pass
        
        return df, info
    except Exception as e:
        return None, {}

def calculate_technical_indicators(df):
    """计算技术指标"""
    d = df.copy()
    
    # 均线
    d['MA5'] = d['Close'].rolling(5).mean()
    d['MA10'] = d['Close'].rolling(10).mean()
    d['MA20'] = d['Close'].rolling(20).mean()
    d['MA60'] = d['Close'].rolling(60).mean()
    
    # MACD
    e1 = d['Close'].ewm(span=12).mean()
    e2 = d['Close'].ewm(span=26).mean()
    d['MACD'] = e1 - e2
    d['Signal'] = d['MACD'].ewm(span=9).mean()
    d['MACD_Hist'] = d['MACD'] - d['Signal']
    
    # RSI
    dl = d['Close'].diff()
    g = dl.where(dl>0,0).rolling(14).mean()
    l = (-dl.where(dl<0,0)).rolling(14).mean()
    d['RSI'] = 100 - (100/(1+g/l))
    
    # KDJ
    low_min = d['Low'].rolling(9).min()
    high_max = d['High'].rolling(9).max()
    d['K'] = 100 * (d['Close'] - low_min) / (high_max - low_min)
    d['D'] = d['K'].rolling(3).mean()
    d['J'] = 3 * d['K'] - 2 * d['D']
    
    # 布林带
    d['BB_Mid'] = d['Close'].rolling(20).mean()
    d['BB_Std'] = d['Close'].rolling(20).std()
    d['BB_Up'] = d['BB_Mid'] + 2 * d['BB_Std']
    d['BB_Down'] = d['BB_Mid'] - 2 * d['BB_Std']
    
    return d

def get_technical_signals(df, current_price):
    """获取技术信号"""
    d = calculate_technical_indicators(df)
    
    signals = {}
    
    # 均线信号
    ma5 = d['MA5'].iloc[-1]
    ma10 = d['MA10'].iloc[-1]
    ma20 = d['MA20'].iloc[-1]
    
    if ma5 > ma10 > ma20:
        signals['MA'] = {"signal": "买入", "reason": "均线多头排列", "color": "green"}
    elif ma5 < ma10 < ma20:
        signals['MA'] = {"signal": "卖出", "reason": "均线空头排列", "color": "red"}
    else:
        signals['MA'] = {"signal": "观望", "reason": "均线震荡", "color": "yellow"}
    
    # MACD信号
    macd = d['MACD'].iloc[-1]
    signal = d['Signal'].iloc[-1]
    
    if macd > signal:
        signals['MACD'] = {"signal": "买入", "reason": "MACD金叉", "color": "green"}
    else:
        signals['MACD'] = {"signal": "卖出", "reason": "MACD死叉", "color": "red"}
    
    # RSI信号
    rsi = d['RSI'].iloc[-1]
    if rsi < 30:
        signals['RSI'] = {"signal": "超卖买入", "reason": f"RSI={rsi:.1f}超卖", "color": "green"}
    elif rsi > 70:
        signals['RSI'] = {"signal": "超买卖出", "reason": f"RSI={rsi:.1f}超买", "color": "red"}
    else:
        signals['RSI'] = {"signal": "观望", "reason": f"RSI={rsi:.1f}中性", "color": "yellow"}
    
    # KDJ信号
    k = d['K'].iloc[-1]
    d_val = d['D'].iloc[-1]
    if k > d_val:
        signals['KDJ'] = {"signal": "买入", "reason": "KDJ金叉", "color": "green"}
    else:
        signals['KDJ'] = {"signal": "卖出", "reason": "KDJ死叉", "color": "red"}
    
    # 布林带信号
    bb_up = d['BB_Up'].iloc[-1]
    bb_down = d['BB_Down'].iloc[-1]
    
    if current_price > bb_up:
        signals['BB'] = {"signal": "超买", "reason": "突破布林上轨", "color": "red"}
    elif current_price < bb_down:
        signals['BB'] = {"signal": "超卖", "reason": "触及布林下轨", "color": "green"}
    else:
        signals['BB'] = {"signal": "观望", "reason": "布林带内运行", "color": "yellow"}
    
    return signals

def render_header():
    """渲染头部"""
    st.markdown('<p class="main-title">📈 股票分析工具 Pro Max</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">支持美股、A股、港股 | V3.1分析框架</p>', unsafe_allow_html=True)

def render_search():
    """渲染搜索框"""
    with st.container():
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 搜索股票",
                placeholder="输入股票代码/名称（如：MSFT、茅台、9988）",
                key="search_input"
            )
        
        with col2:
            period = st.selectbox(
                "📅 分析周期",
                ["1个月", "3个月", "6个月", "1年", "2年"],
                index=3,
                key="period_select"
            )
        
        with col3:
            st.write("")  # 占位
            st.write("")  # 占位
        
        # 搜索建议
        if search_query:
            suggestions = fuzzy_search(search_query, 5)
            if suggestions:
                st.markdown("**💡 您可能想找：**")
                cols = st.columns(len(suggestions))
                for i, s in enumerate(suggestions):
                    with cols[i]:
                        market_emoji = {"US": "🇺🇸", "A": "🇨🇳", "HK": "🇭🇰"}.get(s["market"], "")
                        st.markdown(f"""
                        <div style="background:#2d2d2d;padding:10px;border-radius:8px;text-align:center;cursor:pointer;">
                            <b>{market_emoji} {s['code']}</b><br>
                            <small>{s['name'][:8]}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return search_query, period

def render_price_overview(df, info, symbol):
    """渲染价格概览"""
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    # 判断涨跌颜色
    price_color = "green" if change >= 0 else "red"
    
    st.markdown(f"""
    <div class="stock-card">
        <h2 style="margin:0;">📊 {symbol} 价格概览</h2>
        <div style="display:flex;justify-content:space-around;margin-top:20px;">
            <div class="metric-card">
                <h3 style="margin:0;color:{price_color};">${current_price:.2f}</h3>
                <small>当前价格</small>
            </div>
            <div class="metric-card">
                <h3 style="margin:0;color:{price_color};">{change:+.2f} ({change_pct:+.1f}%)</h3>
                <small>涨跌幅</small>
            </div>
            <div class="metric-card">
                <h3 style="margin:0;">${float(df['High'].max()):.2f}</h3>
                <small>最高价</small>
            </div>
            <div class="metric-card">
                <h3 style="margin:0;">${float(df['Low'].min()):.2f}</h3>
                <small>最低价</small>
            </div>
            <div class="metric-card">
                <h3 style="margin:0;">{float(df['Volume'].iloc[-1])/1e6:.2f}M</h3>
                <small>成交量</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_chart(df, symbol):
    """渲染K线图"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol
    )])
    
    # 添加均线
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='yellow', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='MA60', line=dict(color='purple', width=1)))
    
    fig.update_layout(
        title=f'{symbol} K线走势',
        template='plotly_dark',
        height=400,
        xaxis_rangeslider_visible=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_technical_analysis(df, current_price):
    """渲染技术分析"""
    signals = get_technical_signals(df, current_price)
    
    st.markdown("### 📈 技术分析")
    
    # 信号汇总
    buy_count = sum(1 for s in signals.values() if s["color"] == "green")
    sell_count = sum(1 for s in signals.values() if s["color"] == "red")
    
    # 综合信号
    if buy_count >= 4:
        overall = "🟢 强烈看涨"
    elif buy_count > sell_count:
        overall = "🟡 偏多"
    elif sell_count > buy_count:
        overall = "🔴 偏空"
    else:
        overall = "⚪ 中性"
    
    st.markdown(f"**综合技术信号**: {overall}")
    
    # 显示各指标
    cols = st.columns(3)
    
    for i, (name, data) in enumerate(signals.items()):
        with cols[i % 3]:
            color = {"green": "🟢", "red": "🔴", "yellow": "🟡"}.get(data["color"], "⚪")
            st.markdown(f"""
            <div style="background:#262730;padding:12px;border-radius:10px;margin:5px 0;">
                <b>{name}</b><br>
                <span style="font-size:18px;">{color} {data['signal']}</span><br>
                <small style="color:#888;">{data['reason']}</small>
            </div>
            """, unsafe_allow_html=True)

def render_fundamental_analysis(info):
    """渲染基本面分析"""
    st.markdown("### 💰 基本面分析")
    
    if not info or not isinstance(info, dict):
        st.warning("暂无基本面数据")
        return
    
    # 关键指标
    pe = info.get('forwardPE') or info.get('trailingPE')
    pb = info.get('priceToBook')
    mc = info.get('marketCap')
    div = info.get('dividendYield')
    roe = info.get('returnOnEquity')
    
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{pe:.1f}' if pe else 'N/A'}</h3>
            <small>市盈率(PE)</small>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.metric("市盈率(PE)", f"{pe:.1f}" if pe else "N/A")
    
    with cols[2]:
        st.metric("市净率(PB)", f"{pb:.1f}" if pb else "N/A")
    
    with cols[3]:
        st.metric("市值", f"${mc/1e9:.0f}B" if mc else "N/A")
    
    # 公司信息
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    
    st.info(f"**行业**: {sector} | **板块**: {industry}")
    
    # 估值判断
    if pe:
        if pe < 15:
            st.success("🟢 PE偏低，价值投资区间")
        elif pe > 40:
            st.error("🔴 PE偏高，注意风险")
        else:
            st.warning("🟡 PE处于合理区间")

def render_conclusion(signals, info):
    """渲染综合结论"""
    st.markdown("### 🎯 综合投资建议")
    
    buy_count = sum(1 for s in signals.values() if s["color"] == "green")
    total = len(signals)
    
    score = (buy_count / total) * 10
    stars = min(10, max(1, int(score)))
    
    st.markdown(f"{'⭐'*stars}{'☆'*(10-stars)} **{stars}/10**")
    
    if stars >= 8:
        st.success("## ✅ 强烈推荐买入\n\n技术面明显多头，可以考虑分批建仓")
    elif stars >= 5:
        st.info("## ⚖️ 中性观望\n\n多空信号均衡，建议等待更明确的方向")
    else:
        st.error("## ⛔ 建议回避\n\n技术面偏空，建议等待风险释放")

def main():
    """主函数"""
    # 渲染头部
    render_header()
    
    # 渲染搜索框
    search_query, period = render_search()
    
    # 映射周期
    period_map = {"1个月": "1mo", "3个月": "3mo", "6个月": "6mo", "1年": "1y", "2年": "2y"}
    period_code = period_map[period]
    
    # 获取股票代码
    if search_query:
        stock_code = get_stock_code(search_query)
    else:
        stock_code = "MSFT"  # 默认
    
    if not stock_code:
        st.error("❌ 无法识别股票代码，请尝试其他输入")
        return
    
    # 获取数据
    with st.spinner('📊 加载数据中...'):
        df, info = get_stock_data(stock_code, period_code)
    
    if df is None or len(df) == 0:
        st.error(f"❌ 无法获取 {stock_code} 数据")
        st.info("试试: MSFT, AAPL, 600060, 9988, 0700")
        return
    
    # 渲染价格概览
    render_price_overview(df, info, stock_code)
    
    # 渲染K线图
    render_chart(df, stock_code)
    
    # 渲染技术分析
    current_price = float(df['Close'].iloc[-1])
    render_technical_analysis(df, current_price)
    
    st.markdown("---")
    
    # 渲染基本面分析
    render_fundamental_analysis(info)
    
    st.markdown("---")
    
    # 渲染综合结论
    signals = get_technical_signals(df, current_price)
    render_conclusion(signals, info)
    
    # 底部信息
    st.markdown("---")
    st.caption(f"⚠️ 免责声明: 本分析仅供参考，不构成投资建议 | 数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: Yahoo Finance")

if __name__ == "__main__":
    main()
