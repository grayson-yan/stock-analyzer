"""
股票综合分析工具 - Streamlit App v2.0
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="股票综合分析工具", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>.main { background-color: #f5f5f5; } .stButton>button { width: 100%; }</style>""", unsafe_allow_html=True)

st.title("📈 股票综合分析工具 Pro")
st.markdown("**技术面 | 基本面 | 估值 | 缠论 | 韦科夫 | 深度调研**")

with st.sidebar:
    st.header("🔍 股票搜索")
    symbol_input = st.text_input("输入股票代码", value="AAPL", key="symbol_input")
    search_btn = st.button("🔎 查询", type="primary")
    
    if search_btn or symbol_input:
        symbol = symbol_input.upper().strip()
    else:
        symbol = "AAPL"
    
    st.markdown("---")
    st.header("📊 时间周期")
    timeframe = st.selectbox("选择周期", ["15分钟", "1小时", "6小时", "日线", "7日", "14日", "30日", "60日", "120日", "180日", "1年", "2年", "3年", "5年", "10年"], index=3)
    
    timeframe_map = {"15分钟": "15m", "1小时": "1h", "6小时": "6h", "日线": "1d", "7日": "7d", "14日": "14d", "30日": "30d", "60日": "60d", "120日": "120d", "180日": "180d", "1年": "1y", "2年": "2y", "3年": "3y", "5年": "5y", "10年": "10y"}
    period = timeframe_map[timeframe]
    
    st.markdown("---")
    st.header("⚙️ 分析模块")
    show_technical = st.checkbox("技术面分析", value=True)
    show_fundamental = st.checkbox("基本面分析", value=True)
    show_valuation = st.checkbox("估值分析", value=True)
    show_chan = st.checkbox("缠论分析", value=True)
    show_wyckoff = st.checkbox("韦科夫量价分析", value=True)
    show_deep = st.checkbox("深度基本面分析", value=True)

@st.cache_data(ttl=300)
def get_stock_data(symbol, period):
    try:
        ticker = yf.Ticker(symbol)
        if period in ["15m", "1h", "6h"]:
            df = ticker.history(period="5d", interval=period)
        else:
            df = ticker.history(period=period)
        try:
            info = ticker.info or {}
        except:
            info = {}
        return df, info
    except:
        return None, {}

df, info = get_stock_data(symbol, period)

if df is None or len(df) == 0:
    st.error(f"❌ 无法获取 {symbol} 的数据")
    st.info("💡 美股用 AAPL、MSFT，中概股用 0700.HK（港股）")
    st.stop()

st.header(f"📊 {symbol} 概览")
try:
    current_price = float(df['Close'].iloc[-1]) if pd.notna(df['Close'].iloc[-1]) else 0
    prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 and pd.notna(df['Close'].iloc[-2]) else current_price
except:
    current_price = 0
    prev_price = 0
    
change = current_price - prev_price
change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("当前价格", f"${current_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
with col2: st.metric("最高价", f"${float(df['High'].max()):.2f}")
with col3: st.metric("最低价", f"${float(df['Low'].min()):.2f}")
with col4: 
    vol = float(df['Volume'].iloc[-1]) if pd.notna(df['Volume'].iloc[-1]) else 0
    st.metric("成交量", f"{vol/1e6:.2f}M" if vol > 1e6 else f"{vol/1e3:.2f}K")

all_signals = {}

st.subheader("📊 K线走势")
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K线')])
fig.update_layout(title=f'{symbol} K线图 ({timeframe})', template='plotly_dark', height=500)
st.plotly_chart(fig, use_container_width=True)

if show_technical:
    st.markdown("---")
    st.header("📈 技术面分析")
    
    df_tech = df.copy()
    df_tech['MA5'] = df_tech['Close'].rolling(window=5).mean()
    df_tech['MA10'] = df_tech['Close'].rolling(window=10).mean()
    df_tech['MA20'] = df_tech['Close'].rolling(window=20).mean()
    df_tech['MA60'] = df_tech['Close'].rolling(window=60).mean()
    
    exp1 = df_tech['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_tech['Close'].ewm(span=26, adjust=False).mean()
    df_tech['MACD'] = exp1 - exp2
    df_tech['Signal'] = df_tech['MACD'].ewm(span=9, adjust=False).mean()
    df_tech['MACD_Hist'] = df_tech['MACD'] - df_tech['Signal']
    
    delta = df_tech['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_tech['RSI'] = 100 - (100 / (1 + rs))
    
    tech_signal = "wait"
    tech_reasons = []
    ma5 = float(df_tech['MA5'].iloc[-1]) if pd.notna(df_tech['MA5'].iloc[-1]) else 0
    ma20 = float(df_tech['MA20'].iloc[-1]) if pd.notna(df_tech['MA20'].iloc[-1]) else 0
    macd = float(df_tech['MACD'].iloc[-1]) if pd.notna(df_tech['MACD'].iloc[-1]) else 0
    sig = float(df_tech['Signal'].iloc[-1]) if pd.notna(df_tech['Signal'].iloc[-1]) else 0
    rsi = float(df_tech['RSI'].iloc[-1]) if pd.notna(df_tech['RSI'].iloc[-1]) else 50
    
    buy_cnt = 0
    if ma5 > ma20: tech_reasons.append("均线多头"); buy_cnt += 1
    else: tech_reasons.append("均线空头")
    if macd > sig: tech_reasons.append("MACD金叉"); buy_cnt += 1
    else: tech_reasons.append("MACD死叉")
    if rsi < 30: tech_reasons.append(f"RSI超卖({rsi:.1f})"); buy_cnt += 1
    elif rsi > 70: tech_reasons.append(f"RSI超买({rsi:.1f})"); buy_cnt -= 1
    
    tech_signal = "buy" if buy_cnt >= 2 else "sell" if buy_cnt <= 0 else "wait"
    all_signals['技术面'] = {'signal': tech_signal, 'reasons': tech_reasons}
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_ma = go.Figure()
        for ma, color in [('MA5','yellow'), ('MA10','orange'), ('MA20','red'), ('MA60','purple')]:
            fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech[ma], name=ma, line=dict(color=color, width=1)))
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'], name='收盘价', line=dict(color='white', width=1)))
        fig_ma.update_layout(title='均线系统', template='plotly_dark', height=300)
        st.plotly_chart(fig_ma, use_container_width=True)
    with col2:
        st.markdown("### 均线信号")
        st.success("▲ 多头" if ma5 > ma20 else "▼ 空头")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_macd = go.Figure()
        colors = ['green' if v >= 0 else 'red' for v in df_tech['MACD_Hist'].fillna(0)]
        fig_macd.add_trace(go.Bar(x=df_tech.index, y=df_tech['MACD_Hist'], marker_color=colors))
        fig_macd.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Signal'], name='Signal', line=dict(color='orange')))
        fig_macd.update_layout(title='MACD', template='plotly_dark', height=250)
        st.plotly_chart(fig_macd, use_container_width=True)
    with col2:
        st.markdown("### MACD信号")
        st.success("▲ 金叉" if macd > sig else "▼ 死叉")
    
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df_tech.index, y=df_tech['RSI'], name='RSI', line=dict(color='purple')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖")
    fig_rsi.update_layout(title='RSI', template='plotly_dark', height=250, yaxis_range=[0, 100])
    st.plotly_chart(fig_rsi, use_container_width=True)
    
    st.markdown(f"**技术面信号：** {'🟢 买入' if tech_signal=='buy' else '🔴 卖出' if tech_signal=='sell' else '🟡 观望'} | {' / '.join(tech_reasons)}")

if show_chan:
    st.markdown("---")
    st.header("🀄 缠论分析")
    
    fractals = {'top': [], 'bottom': []}
    if len(df) >= 5:
        for i in range(2, len(df) - 2):
            if df['High'].iloc[i-2] < df['High'].iloc[i-1] > df['High'].iloc[i] < df['High'].iloc[i+1] > df['High'].iloc[i+2]:
                fractals['top'].append((df.index[i], df['High'].iloc[i]))
            if df['Low'].iloc[i-2] > df['Low'].iloc[i-1] < df['Low'].iloc[i] > df['Low'].iloc[i+1] < df['Low'].iloc[i+2]:
                fractals['bottom'].append((df.index[i], df['Low'].iloc[i]))
    
    top_c, bot_c = len(fractals['top']), len(fractals['bottom'])
    chan_signal = "buy" if bot_c > top_c else "sell" if top_c > bot_c else "wait"
    chan_reasons = [f"顶分型:{top_c}", f"底分型:{bot_c}"]
    
    recent_high = float(df['High'].tail(20).max()) if len(df) >= 20 else float(df['High'].max())
    recent_low = float(df['Low'].tail(20).min()) if len(df) >= 20 else float(df['Low'].min())
    position = (current_price - recent_low) / (recent_high - recent_low) * 100 if recent_high > recent_low else 50
    chan_reasons.append(f"区间位置:{position:.0f}%")
    
    all_signals['缠论'] = {'signal': chan_signal, 'reasons': chan_reasons}
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 分型信号")
        st.info(f"顶分型: {top_c} | 底分型: {bot_c}")
    with col2:
        st.markdown("#### 走势位置")
        st.progress(position/100)
        st.caption(f"当前在近期区间: {position:.1f}%")
    
    fig_c = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K线')])
    if fractals['top']:
        tx, ty = zip(*fractals['top'][-10:])
        fig_c.add_trace(go.Scatter(x=tx, y=ty, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='顶分型'))
    if fractals['bottom']:
        bx, by = zip(*fractals['bottom'][-10:])
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='底分型'))
    fig_c.update_layout(title='缠论分型标注', template='plotly_dark', height=400)
    st.plotly_chart(fig_c, use_container_width=True)
    
    st.markdown("**缠论说明：** 🟢底分型=下跌结束可能反转 | 🔴顶分型=上涨结束可能回落")
    st.markdown(f"**缠论信号：** {'🟢 买入' if chan_signal=='buy' else '🔴 卖出' if chan_signal=='sell' else '🟡 观望'} | {' / '.join(chan_reasons)}")

if show_wyckoff:
    st.markdown("---")
    st.header("📊 韦科夫量价分析")
    
    df_w = df.copy()
    df_w['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
    df_w['VWAP'] = (df_w['TypicalPrice'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    vwap = float(df_w['VWAP'].iloc[-1]) if pd.notna(df_w['VWAP'].iloc[-1]) else current_price
    avg_v = float(df['Volume'].tail(20).mean()) if pd.notna(df['Volume'].tail(20).mean()) else 1
    vol_r = float(df['Volume'].iloc[-1]) / avg_v if avg_v > 0 else 1
    
    wyckoff_signal = "buy" if current_price > vwap and vol_r > 0.8 else "sell" if current_price < vwap else "wait"
    wyckoff_reasons = [f"{'上方' if current_price > vwap else '下方'}VWAP", f"量比:{vol_r:.2f}x"]
    if vol_r > 1.5: wyckoff_reasons.append("放量")
    elif vol_r < 0.5: wyckoff_reasons.append("缩量")
    
    all_signals['韦科夫'] = {'signal': wyckoff_signal, 'reasons': wyckoff_reasons}
    
    col1, col2 = st.columns(2)
    with col1: st.success("▲ 上升趋势" if current_price > vwap else "▼ 下降趋势")
    with col2: st.info(f"量比: {vol_r:.2f}x")
    
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=df_w.index, y=df_w['Close'], name='收盘价', line=dict(color='white')))
    fig_v.add_trace(go.Scatter(x=df_w.index, y=df_w['VWAP'], name='VWAP', line=dict(color='yellow', width=2)))
    fig_v.update_layout(title='价格 vs VWAP', template='plotly_dark', height=300)
    st.plotly_chart(fig_v, use_container_width=True)
    
    st.markdown(f"**韦科夫信号：** {'🟢 买入' if wyckoff_signal=='buy' else '🔴 卖出' if wyckoff_signal=='sell' else '🟡 观望'} | {' / '.join(wyckoff_reasons)}")

if show_fundamental:
    st.markdown("---")
    st.header("💰 基本面分析")
    
    fund_signal = "wait"
    fund_reasons = []
    pe = None
    
    if info and isinstance(info, dict):
        pe = info.get('forwardPE') or info.get('trailingPE')
        if pe and isinstance(pe, (int, float)):
            if pe < 15: fund_signal = "buy"; fund_reasons.append(f"PE低({pe:.1f})")
            elif pe > 40: fund_signal = "sell"; fund_reasons.append(f"PE1f})")
高({pe:.            else: fund_reasons.append(f"PE({pe:.1f})")
        
        all_signals['基本面'] = {'signal': fund_signal, 'reasons': fund_reasons}
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("PE", f"{pe:.2f}" if pe else "N/A")
        with col2: st.metric("PB", f"{info.get('priceToBook', 'N/A')}" if info else "N/A")
        with col3: 
            mc = info.get('marketCap') if info else None
            st.metric("市值", f"${mc/1e9:.1f}B" if mc else "N/A")
        with col4: 
            dy = info.get('dividendYield') if info else None
            st.metric("股息率", f"{dy*100:.2f}%" if dy else "N/A")
        
        st.markdown(f"**基本面信号：** {'🟢 买入' if fund_signal=='buy' else '🔴 卖出' if fund_signal=='sell' else '🟡 观望'} | {' / '.join(fund_reasons) if fund_reasons else '数据不足'}")

if show_valuation:
    st.markdown("---")
    st.header("🎯 估值分析")
    
    val_signal = "wait"
    val_reasons = []
    dcf = None
    pos = None
    
    if info and isinstance(info, dict):
        pe = info.get('forwardPE') or info.get('trailingPE')
        eps = info.get('epsTrailingTwelveMonths')
        if pe and eps:
            growth = info.get('earningsGrowth') or 0
            if isinstance(growth, (int, float)):
                dcf = eps * (1 + growth) * (1.02 / 0.08)
                val_reasons.append(f"DCF估值: ${dcf:.2f}")
        
        high52 = info.get('fiftyTwoWeekHigh')
        low52 = info.get('fiftyTwoWeekLow')
        if high52 and low52:
            pos = (current_price - low52) / (high52 - low52) * 100
            val_reasons.append(f"52周位置: {pos:.0f}%")
            if pos > 80: val_signal = "sell"
            elif pos < 20: val_signal = "buy"
        
        all_signals['估值'] = {'signal': val_signal, 'reasons': val_reasons}
        
        col1, col2 = st.columns(2)
        with col1: 
            if dcf: st.success(f"📊 DCF估值: ${dcf:.2f}")
        with col2:
            if pos: 
                st.progress(pos/100)
                st.caption(f"52周位置: {pos:.1f}%")
        
        st.markdown(f"**估值信号：** {'🟢 买入' if val_signal=='buy' else '🔴 卖出' if val_signal=='sell' else '🟡 观望'}")

if show_deep:
    st.markdown("---")
    st.header("🔬 深度基本面分析")
    
    deep_signal = "wait"
    deep_reasons = []
    
    if info and isinstance(info, dict):
        st.markdown("### 一、主营业务（赚钱的底色）")
        
        sector = info.get('sector', 'N/A') if info else 'N/A'
        industry = info.get('industry', 'N/A') if info else 'N/A'
        business = info.get('businessSummary', '暂无')[:300] if info else '暂无'
        
        col1, col2 = st.columns(2)
        with col1: st.metric("行业", sector)
        with col2: st.metric("子行业", industry)
        st.info(f"业务: {business}...")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rev = info.get('totalRevenue')
            if rev: st.metric("营收", f"${rev/1e9:.1f}B"); deep_reasons.append(f"营收{rev/1e9:.0f}B")
        with col2:
            gm = info.get('grossMargins')
            if gm: st.metric("毛利率", f"{gm*100:.1f}%"); deep_reasons.append(f"毛利{gm*100:.0f}%")
        with col3:
            pm = info.get('profitMargins')
            if pm: st.metric("净利率", f"{pm*100:.1f}%")
        with col4:
            roe = info.get('returnOnEquity')
            if roe: st.metric("ROE", f"{roe*100:.1f}%"); deep_reasons.append(f"ROE{roe*100:.0f}%")
        
        st.markdown("### 二、市场占有（护城河）")
        
        col1, col2 = st.columns(2)
        with col1:
            mc = info.get('marketCap')
            if mc: st.metric("市值", f"${mc/1e9:.1f}B")
        with col2:
            beta = info.get('beta')
            if beta: st.metric("Beta", f"{beta:.2f}")
        
        st.markdown("### 三、竞争与技术")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rd = info.get('researchAndDevelopment')
            if rd: st.metric("研发", f"${rd/1e9:.1f}B")
        with col2:
            debt = info.get('debtToEquity')
            if debt: st.metric("负债率", f"{debt:.1f}%")
        with col3:
            cf = info.get('operatingCashflow')
            if cf: st.metric("经营现金流", f"${cf/1e9:.1f}B")
        with col4:
            fcf = info.get('freeCashflow')
            if fcf: st.metric("自由现金流", f"${fcf/1e9:.1f}B")
        
        if gm and gm > 0.4: deep_signal = "buy"
        if roe and roe > 0.15: deep_signal = "buy"
        
        all_signals['深度基本面'] = {'signal': deep_signal, 'reasons': deep_reasons}
        
        st.markdown(f"**深度基本面信号：** {'🟢 买入' if deep_signal=='buy' else '🟡 观望'}")

st.markdown("---")
st.header("⭐ 综合评级")

buy_cnt = sum(1 for v in all_signals.values() if v['signal'] == 'buy')
sell_cnt = sum(1 for v in all_signals.values() if v['signal'] == 'sell')
wait_cnt = sum(1 for v in all_signals.values() if v['signal'] == 'wait')

total = len(all_signals)
star_cnt = max(1, min(10, buy_cnt * 3 + (total - buy_cnt - sell_cnt) * 1))

st.markdown(f"### {'⭐' * star_cnt}{'☆' * (10-star_cnt)} **{star_cnt}/10**")

col1, col2, col3 = st.columns(3)
with col1: st.success(f"🟢 买入信号: {buy_cnt}")
with col2: st.error(f"🔴 卖出信号: {sell_cnt}")
with col3: st.warning(f"🟡 观望信号: {wait_cnt}")

if star_cnt >= 7:
    st.success("⭐ **强烈推荐买入** - 多项指标显示积极信号")
elif star_cnt >= 4:
    st.info("⭐ **中性观望** - 建议等待更明确信号")
else:
    st.error("⭐ **建议回避** - 多项指标显示风险")

st.markdown("---")
st.header("📅 不同周期投资评级")

periods = [("超短线(15分)", "15m"), ("短线(1小时)", "1h"), ("短波(6小时)", "6h"), ("日内(1日)", "1d"), ("1周内", "7d"), ("1月内", "30d"), ("季度", "90d"), ("半年", "180d"), ("1年", "1y"), ("长线(2年+)", "2y")]

results = []
for name, p in periods:
    try:
        temp_df = yf.Ticker(symbol).history(period="max" if p in ["1y","2y"] else "2y", interval=p if p in ["15m","1h","6h"] else "1d")
        if temp_df is not None and len(temp_df) > 10:
            ma5 = float(temp_df['Close'].rolling(5).mean().iloc[-1]) if pd.notna(temp_df['Close'].rolling(5).mean().iloc[-1]) else 0
            ma20 = float(temp_df['Close'].rolling(20).mean().iloc[-1]) if pd.notna(temp_df['Close'].rolling(20).mean().iloc[-1]) else 0
            if ma20 != 0:
                sig = "⭐⭐⭐⭐⭐" if ma5 > ma20 else "⭐⭐⭐" if abs(ma5-ma20)/ma20 < 0.02 else "⭐⭐"
                results.append((name, sig, "🟢" if ma5 > ma20 else "🔴"))
            else:
                results.append((name, "⭐⭐⭐", "🟡"))
    except:
        results.append((name, "⭐⭐⭐", "🟡"))

cols = st.columns(2)
for i, (name, stars, status) in enumerate(results):
    with cols[i % 2]:
        st.markdown(f"**{name}**: {stars} {status}")

st.markdown("---")
st.caption(f"📊 数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据源: Yahoo Finance | 仅供参考，不构成投资建议")
