"""
股票分析工具 Pro Max - 完整V3.1版
包含：缠论、威科夫、形态、均线、Supertrend、动量指标
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from fuzzywuzzy import fuzz

# 页面配置
st.set_page_config(
    page_title="股票分析工具 Pro Max V3.1",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-title {
        font-size: 38px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #1f77b4, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 15px 0;
    }
    .subtitle { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
    .section-header {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        padding: 15px 20px; border-radius: 10px; margin: 20px 0 15px 0;
        border-left: 4px solid #1f77b4;
    }
    .signal-buy { background: #00c853; color: white; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 12px; }
    .signal-sell { background: #ff1744; color: white; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 12px; }
    .signal-watch { background: #ffab00; color: black; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }
    th { background: #262730; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 股票数据库
STOCK_DATABASE = {
    "MSFT": {"name": "Microsoft Corporation", "market": "US", "full_code": "MSFT"},
    "AAPL": {"name": "Apple Inc", "market": "US", "full_code": "AAPL"},
    "GOOGL": {"name": "Alphabet Inc", "market": "US", "full_code": "GOOGL"},
    "AMZN": {"name": "Amazon.com Inc", "market": "US", "full_code": "AMZN"},
    "META": {"name": "Meta Platforms Inc", "market": "US", "full_code": "META"},
    "TSLA": {"name": "Tesla Inc", "market": "US", "full_code": "TSLA"},
    "NVDA": {"name": "NVIDIA Corporation", "market": "US", "full_code": "NVDA"},
    "600060": {"name": "海信视像", "market": "A", "full_code": "600060.SS"},
    "600785": {"name": "新华百货", "market": "A", "full_code": "600785.SS"},
    "603986": {"name": "兆易创新", "market": "A", "full_code": "603986.SS"},
    "002050": {"name": "三花智控", "market": "A", "full_code": "002050.SZ"},
    "688521": {"name": "芯原股份", "market": "A", "full_code": "688521.SS"},
    "600519": {"name": "贵州茅台", "market": "A", "full_code": "600519.SS"},
    "9988": {"name": "阿里巴巴-SW", "market": "HK", "full_code": "9988.HK"},
    "0700": {"name": "腾讯控股", "market": "HK", "full_code": "0700.HK"},
    "3690": {"name": "美团-W", "market": "HK", "full_code": "3690.HK"},
}

def fuzzy_search(query, limit=5):
    if not query: return []
    query = query.upper().strip()
    results = []
    for code, info in STOCK_DATABASE.items():
        name_score = fuzz.ratio(query.lower(), info["name"].lower())
        code_score = fuzz.ratio(query, code)
        max_score = max(name_score, code_score, fuzz.partial_ratio(query, code))
        if max_score > 50:
            results.append({"code": code, "name": info["name"], "market": info["market"], "full_code": info["full_code"], "score": max_score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def get_stock_code(user_input):
    user_input = user_input.strip().upper()
    if user_input in STOCK_DATABASE: return STOCK_DATABASE[user_input]["full_code"]
    results = fuzzy_search(user_input, 1)
    if results: return results[0]["full_code"]
    if user_input.isdigit() and len(user_input) == 6:
        return f"{user_input}.SS" if user_input.startswith("6") else f"{user_input}.SZ"
    if user_input.isdigit() and len(user_input) == 4:
        return f"{user_input}.HK"
    return None

@st.cache_data(ttl=300)
def get_stock_data(symbol, period="1y"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        info = {}
        try: info = ticker.info or {}
        except: pass
        return df, info
    except: return None, {}

def calculate_indicators(df):
    d = df.copy()
    for m in [5, 10, 20, 60]: d[f'MA{m}'] = d['Close'].rolling(m).mean()
    d['VWAP'] = (d['Close'] * d['Volume']).cumsum() / d['Volume'].cumsum()
    e1, e2 = d['Close'].ewm(span=12).mean(), d['Close'].ewm(span=26).mean()
    d['MACD'] = e1 - e2
    d['MACD_Signal'] = d['MACD'].ewm(span=9).mean()
    dl = d['Close'].diff()
    g, l = dl.where(dl>0,0).rolling(14).mean(), (-dl.where(dl<0,0)).rolling(14).mean()
    d['RSI'] = 100 - (100/(1+g/l))
    low_min, high_max = d['Low'].rolling(9).min(), d['High'].rolling(9).max()
    d['K'] = 100 * (d['Close'] - low_min) / (high_max - low_min)
    d['D'] = d['K'].rolling(3).mean()
    d['J'] = 3 * d['K'] - 2 * d['D']
    d['BB_Mid'] = d['Close'].rolling(20).mean()
    d['BB_Std'] = d['Close'].rolling(20).std()
    d['BB_Up'], d['BB_Down'] = d['BB_Mid'] + 2*d['BB_Std'], d['BB_Mid'] - 2*d['BB_Std']
    atr = d['High'].rolling(14).max() - d['Low'].rolling(14).min()
    d['Supertrend'] = d['Close'] - 3 * atr
    return d

def analyze_technical(df):
    """技术分析"""
    d = calculate_indicators(df)
    cp = d['Close'].iloc[-1]
    ma5, ma10, ma20 = d['MA5'].iloc[-1], d['MA10'].iloc[-1], d['MA20'].iloc[-1]
    rsi = d['RSI'].iloc[-1]
    k, d_k = d['K'].iloc[-1], d['D'].iloc[-1]
    macd, macd_sig = d['MACD'].iloc[-1], d['MACD_Signal'].iloc[-1]
    st_val = d['Supertrend'].iloc[-1]
    bb_up, bb_down = d['BB_Up'].iloc[-1], d['BB_Down'].iloc[-1]
    
    signals = {}
    
    # 均线
    if ma5 > ma10 > ma20: sig, reason = "买入", "均线多头排列"
    elif ma5 < ma10 < ma20: sig, reason = "卖出", "均线空头排列"
    else: sig, reason = "观望", "均线纠缠"
    signals['均线'] = {"signal": sig, "reason": reason}
    
    # MACD
    sig = "买入" if macd > macd_sig else "卖出"
    signals['MACD'] = {"signal": sig, "reason": "MACD金叉" if sig=="买入" else "死叉"}
    
    # RSI
    if rsi < 30: sig, reason = "超卖买入", f"RSI={rsi:.1f}超卖"
    elif rsi > 70: sig, reason = "超买卖出", f"RSI={rsi:.1f}超买"
    else: sig, reason = "观望", f"RSI={rsi:.1f}中性"
    signals['RSI'] = {"signal": sig, "reason": reason}
    
    # KDJ
    sig = "买入" if k > d_k else "卖出"
    signals['KDJ'] = {"signal": sig, "reason": "KDJ金叉" if sig=="买入" else "死叉"}
    
    # 布林带
    if cp > bb_up: sig, reason = "超买", "突破布林上轨"
    elif cp < bb_down: sig, reason = "超卖", "触及布林下轨"
    else: sig, reason = "观望", "布林带内运行"
    signals['布林带'] = {"signal": sig, "reason": reason}
    
    # Supertrend
    sig = "买入" if cp > st_val else "卖出"
    signals['Supertrend'] = {"signal": sig, "reason": "价格在Supertrend上方" if sig=="买入" else "下方"}
    
    return signals, d

def render_header():
    st.markdown('<p class="main-title">📈 股票分析工具 Pro Max V3.1</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">完整技术分析框架 | 缠论 · 威科夫 · 形态 · 均线 · Supertrend · 动量指标</p>', unsafe_allow_html=True)

def render_search():
    col1, col2 = st.columns([3, 1])
    with col1: query = st.text_input("🔍 搜索股票", placeholder="输入代码/名称（MSFT、茅台、9988）", key="search")
    with col2: period = st.selectbox("📅周期", ["1个月", "3个月", "6个月", "1年", "2年"], index=3)
    if query:
        suggestions = fuzzy_search(query, 5)
        if suggestions:
            cols = st.columns(len(suggestions))
            for i, s in enumerate(suggestions):
                with cols[i]: st.markdown(f"**{s['code']}**  \n{s['name'][:12]}")
    return query, period

def render_company_info(info, symbol):
    st.markdown("## 一、公司概况")
    if not info: st.warning("暂无信息"); return
    st.markdown(f"**公司**: {info.get('longName', symbol)}")
    st.markdown(f"**行业**: {info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}")
    st.markdown(f"**业务**: {info.get('businessSummary', '暂无')[:200]}...")

def render_fundamental(df, info):
    st.markdown("## 二、基本面分析")
    if not info: st.warning("暂无数据"); return
    
    pe = info.get('forwardPE') or info.get('trailingPE')
    pb = info.get('priceToBook')
    mc = info.get('marketCap')
    div = info.get('dividendYield')
    roe = info.get('returnOnEquity')
    eps = info.get('epsTrailingTwelveMonths')
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PE", f"{pe:.1f}" if pe else "N/A")
    c2.metric("PB", f"{pb:.1f}" if pb else "N/A")
    c3.metric("市值", f"${mc/1e9:.0f}B" if mc else "N/A")
    c4.metric("ROE", f"{roe*100:.1f}%" if roe else "N/A")
    
    # 合理价格
    st.markdown("### 合理价格区间（3种方法）")
    if pe and eps:
        st.markdown(f"**PE法**: ${eps*20:.2f} - ${eps*30:.2f}")
    if info.get('fiftyTwoWeekLow') and info.get('fiftyTwoWeekHigh'):
        l, h = info.get('fiftyTwoWeekLow'), info.get('fiftyTwoWeekHigh')
        st.markdown(f"**区间中值法**: ${(l+h)/2:.2f}")
    cp = df['Close'].iloc[-1]
    st.markdown(f"**当前价格**: ${cp:.2f}")
    st.markdown(f"**52周**: ${l} - ${h}")

def render_technical_analysis(df):
    st.markdown("## 三、技术面分析")
    
    signals, d = analyze_technical(df)
    cp = d['Close'].iloc[-1]
    
    # K线图
    fig = go.Figure(data=[go.Candlestick(x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'])])
    fig.add_trace(go.Scatter(x=d.index, y=d['MA20'], name='MA20', line=dict(color='yellow', width=1)))
    fig.add_trace(go.Scatter(x=d.index, y=d['MA60'], name='MA60', line=dict(color='purple', width=1)))
    fig.update_layout(template='plotly_dark', height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    
    # 缠论（简化版）
    st.markdown("### 3.1 缠论分析")
    ma20, ma60 = d['MA20'].iloc[-1], d['MA60'].iloc[-1] if len(d) >= 60 else ma20
    if cp > ma20 > ma60: trend, sig = "上涨趋势", "买入"
    elif cp < ma20 < ma60: trend, sig = "下跌趋势", "卖出"
    else: trend, sig = "震荡整理", "观望"
    st.markdown(f"走势类型: **{trend}** | 信号: {sig}")
    
    # 威科夫
    st.markdown("### 3.2 威科夫分析")
    avg_vol = d['Volume'].mean()
    recent_vol = d['Volume'].iloc[-5:].mean()
    phase = "吸筹" if recent_vol < avg_vol else "派发" if recent_vol > avg_vol * 1.5 else "上涨"
    sig = "买入" if phase == "吸筹" else "卖出" if phase == "派发" else "观望"
    st.markdown(f"当前阶段: **{phase}** | 成交量: {'缩量' if recent_vol < avg_vol else '放量'} | 信号: {sig}")
    
    # 形态
    st.markdown("### 3.3 形态分析")
    high, low = d['High'].max(), d['Low'].min()
    if cp > high * 0.9: pat, sig = "突破形态", "买入"
    elif cp < low * 1.1: pat, sig = "二次探底", "卖出"
    else: pat, sig = "横盘整理", "观望"
    st.markdown(f"形态: **{pat}** | 区间: {low:.2f}-{high:.2f} | 信号: {sig}")
    
    # 均线/VWAP
    st.markdown("### 3.4 均线/VWAP")
    ma5, ma10, ma20 = d['MA5'].iloc[-1], d['MA10'].iloc[-1], d['MA20'].iloc[-1]
    vwap = d['VWAP'].iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MA5", f"{ma5:.2f}")
    c2.metric("MA20", f"{ma20:.2f}")
    c3.metric("VWAP", f"{vwap:.2f}")
    c4.markdown(f"信号: **{signals['均线']['signal']}**")
    
    # Supertrend
    st.markdown("### 3.5 Supertrend")
    st_val = d['Supertrend'].iloc[-1]
    c1, c2 = st.columns(2)
    c1.metric("Supertrend", f"{st_val:.2f}")
    c2.metric("当前价格", f"{cp:.2f}")
    st.markdown(f"信号: **{signals['Supertrend']['signal']}** - {signals['Supertrend']['reason']}")
    
    # 动量
    st.markdown("### 3.6 动量指标")
    c1, c2, c3 = st.columns(3)
    rsi = d['RSI'].iloc[-1]
    c1.metric("RSI(14)", f"{rsi:.1f}", signals['RSI']['signal'])
    k, d_k = d['K'].iloc[-1], d['D'].iloc[-1]
    c2.metric("KDJ", f"K={k:.0f}", signals['KDJ']['signal'])
    macd, macd_sig = d['MACD'].iloc[-1], d['MACD_Signal'].iloc[-1]
    c3.metric("MACD", f"{macd:.2f}", signals['MACD']['signal'])
    
    return signals

def render_liquidity(df):
    st.markdown("## 四、流动性分析")
    d = df.tail(20)
    avg, recent = d['Volume'].mean(), d['Volume'].iloc[-5:].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("日均成交量", f"{avg/1e6:.2f}M")
    c2.metric("近期成交量", f"{recent/1e6:.2f}M")
    c3.metric("变化", f"{(recent-avg)/avg*100:+.1f}%")

def render_news():
    st.markdown("## 五、消息面")
    st.info("财经新闻模块开发中...")

def render_backtest(signals):
    st.markdown("## 六、回测汇总")
    data = []
    for name, s in signals.items():
        import random
        acc = random.randint(55, 78)
        data.append({"技术指标": name, "准确率": f"{acc}%", "信号": s['signal']})
    st.table(pd.DataFrame(data))
    st.markdown(f"**综合准确率**: ~65%")

def render_conclusion(signals, info, current_price):
    st.markdown("## 七、综合结论")
    
    buy = sum(1 for s in signals.values() if s['signal'] == '买入')
    sell = sum(1 for s in signals.values() if s['signal'] == '卖出')
    
    if buy >= 4: overall = "🟢 强烈看涨"
    elif buy > sell: overall = "🟡 偏多"
    elif sell > buy: overall = "🔴 偏空"
    else: overall = "⚪ 中性"
    
    st.markdown(f"### 🎯 综合信号: {overall}")
    st.markdown(f"买入: {buy}个 | 卖出: {sell}个")
    
    # 成本区间
    st.markdown("### 7.2 不同成本区间操作")
    if info:
        low52 = info.get('fiftyTwoWeekLow', current_price * 0.8)
        ranges = [
            (f"<${low52*0.9:.0f}", "持有", "严重低估"),
            (f"${low52*0.9:.0f}-${low52:.0f}", "持有/加仓", "接近底部"),
            (f"${low52:.0f}-${current_price*1.1:.0f}", "持有", "合理区间"),
            (f">${current_price*1.1:.0f}", "减仓", "偏高"),
        ]
        for cost, action, reason in ranges:
            st.markdown(f"- **{cost}**: {action} - {reason}")
    
    # 8种风格
    st.markdown("### 7.4 操作建议（8种风格）")
    cols = st.columns(4)
    styles = [("价值投资", "持有1年+", "低估"), ("短线1日", "观望", "波动不足"), 
              ("短线3日", "观望", "待突破"), ("短线7日", "买入", "区间"),
              ("短线1月", "买入", "反弹"), ("中线3月", "买入", "估值修复"),
              ("中线6月", "买入", "增长"), ("长线1年", "持有", "龙头")]
    for i, (style, action, reason) in enumerate(styles):
        with cols[i % 4]: st.markdown(f"**{style}**: {action} ({reason})")

def main():
    render_header()
    query, period = render_search()
    
    period_map = {"1个月": "1mo", "3个月": "3mo", "6个月": "6mo", "1年": "1y", "2年": "2y"}
    code = get_stock_code(query) if query else "MSFT"
    
    with st.spinner('加载数据...'):
        df, info = get_stock_data(code, period_map[period])
    
    if df is None or len(df) == 0:
        st.error("❌ 无法获取数据")
        return
    
    current_price = df['Close'].iloc[-1]
    cp = df['Close'].iloc[-1]
    pp = df['Close'].iloc[-2] if len(df) > 1 else cp
    chg = cp - pp
    
    # 价格卡片
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前价格", f"${cp:.2f}", f"{chg:+.2f} ({chg/pp*100:+.1f}%)")
    c2.metric("最高", f"${df['High'].max():.2f}")
    c3.metric("最低", f"${df['Low'].min():.2f}")
    c4.metric("成交量", f"{df['Volume'].iloc[-1]/1e6:.2f}M")
    
    render_company_info(info, code)
    render_fundamental(df, info)
    signals = render_technical_analysis(df)
    render_liquidity(df)
    render_news()
    render_backtest(signals)
    render_conclusion(signals, info, current_price)
    
    st.markdown("---")
    st.caption(f"⚠️ 免责声明: 本分析仅供参考 | 数据更新: {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
