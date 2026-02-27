"""
股票综合分析工具 - Streamlit App
支持：技术面、基本面、估值、缠论、韦科夫量价分析
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="股票综合分析工具",
    page_icon="📈",
    layout="wide"
)

# ==================== 样式 ====================
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .analysis-section {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 标题 ====================
st.title("📈 股票综合分析工具")
st.markdown("**技术面 | 基本面 | 估值 | 缠论 | 韦科夫量价分析**")

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("🔍 股票搜索")
    symbol = st.text_input("输入股票代码", value="AAPL").upper().strip()
    
    st.markdown("---")
    st.header("⚙️ 分析选项")
    show_technical = st.checkbox("技术面分析", value=True)
    show_fundamental = st.checkbox("基本面分析", value=True)
    show_valuation = st.checkbox("估值分析", value=True)
    show_chan = st.checkbox("缠论分析", value=True)
    show_wyckoff = st.checkbox("韦科夫量价分析", value=True)
    
    st.markdown("---")
    st.header("📊 时间周期")
    period = st.selectbox("时间周期", 
        ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=4)

# ==================== 数据获取 ====================
@st.cache_data(ttl=3600)
def get_stock_data(symbol, period):
    """获取股票数据"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        info = stock.info
        return df, info, stock
    except Exception as e:
        return None, None, None

df, info, stock = get_stock_data(symbol, period)

if df is None or df.empty:
    st.error(f"❌ 无法获取 {symbol} 的数据，请检查股票代码是否正确")
    st.stop()

# ==================== 股票基本信息 ====================
col1, col2, col3, col4 = st.columns(4)
current_price = df['Close'].iloc[-1]
prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
change = current_price - prev_price
change_pct = (change / prev_price) * 100

with col1:
    st.metric("当前价格", f"${current_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
with col2:
    st.metric("最高价", f"${df['High'].max():.2f}")
with col3:
    st.metric("最低价", f"${df['Low'].min():.2f}")
with col4:
    st.metric("成交量", f"{df['Volume'].iloc[-1]:,.0f}")

st.markdown("---")

# ==================== K线图 ====================
def plot_candlestick(df):
    """绘制K线图"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K线'
    )])
    
    fig.update_layout(
        title=f'{symbol} K线图',
        yaxis_title='价格',
        xaxis_title='日期',
        template='plotly_dark',
        height=500
    )
    
    return fig

st.subheader("📊 K线走势")
st.plotly_chart(plot_candlestick(df), use_container_width=True)

# ==================== 技术指标 ====================
if show_technical:
    st.markdown("---")
    st.header("📈 技术面分析")
    
    # 计算技术指标
    df_tech = df.copy()
    
    # 均线
    df_tech['MA5'] = df_tech['Close'].rolling(window=5).mean()
    df_tech['MA10'] = df_tech['Close'].rolling(window=10).mean()
    df_tech['MA20'] = df_tech['Close'].rolling(window=20).mean()
    df_tech['MA60'] = df_tech['Close'].rolling(window=60).mean()
    
    # MACD
    exp1 = df_tech['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_tech['Close'].ewm(span=26, adjust=False).mean()
    df_tech['MACD'] = exp1 - exp2
    df_tech['Signal'] = df_tech['MACD'].ewm(span=9, adjust=False).mean()
    df_tech['MACD_Hist'] = df_tech['MACD'] - df_tech['Signal']
    
    # RSI
    delta = df_tech['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_tech['RSI'] = 100 - (100 / (1 + rs))
    
    # 布林带
    df_tech['BB_Middle'] = df_tech['Close'].rolling(window=20).mean()
    df_tech['BB_Std'] = df_tech['Close'].rolling(window=20).std()
    df_tech['BB_Upper'] = df_tech['BB_Middle'] + 2 * df_tech['BB_Std']
    df_tech['BB_Lower'] = df_tech['BB_Middle'] - 2 * df_tech['BB_Std']
    
    # 展示均线
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA5'], name='MA5', line=dict(color='yellow', width=1)))
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA10'], name='MA10', line=dict(color='orange', width=1)))
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA20'], name='MA20', line=dict(color='red', width=1)))
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA60'], name='MA60', line=dict(color='purple', width=1)))
        fig_ma.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'], name='收盘价', line=dict(color='white', width=1)))
        fig_ma.update_layout(title='均线系统', template='plotly_dark', height=300)
        st.plotly_chart(fig_ma, use_container_width=True)
    
    with col2:
        st.markdown("### 均线信号")
        ma5 = df_tech['MA5'].iloc[-1]
        ma20 = df_tech['MA20'].iloc[-1]
        if ma5 > ma20:
            st.success("▲ 多头排列")
        elif ma5 < ma20:
            st.error("▼ 空头排列")
        else:
            st.warning("▬ 震荡整理")
    
    # 展示MACD
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_macd = go.Figure()
        colors = ['green' if v >= 0 else 'red' for v in df_tech['MACD_Hist'].fillna(0)]
        fig_macd.add_trace(go.Bar(x=df_tech.index, y=df_tech['MACD_Hist'], name='MACD柱', marker_color=colors))
        fig_macd.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MACD'], name='MACD', line=dict(color='blue', width=1)))
        fig_macd.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Signal'], name='Signal', line=dict(color='orange', width=1)))
        fig_macd.update_layout(title='MACD', template='plotly_dark', height=250)
        st.plotly_chart(fig_macd, use_container_width=True)
    
    with col2:
        st.markdown("### MACD信号")
        macd = df_tech['MACD'].iloc[-1]
        signal = df_tech['Signal'].iloc[-1]
        if macd > signal:
            st.success("▲ 金叉买入")
        elif macd < signal:
            st.error("▼ 死叉卖出")
        else:
            st.warning("▬ 等待信号")
    
    # 展示RSI
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df_tech.index, y=df_tech['RSI'], name='RSI', line=dict(color='purple', width=1)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖")
        fig_rsi.update_layout(title='RSI', template='plotly_dark', height=250, yaxis_range=[0, 100])
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        st.markdown("### RSI信号")
        rsi = df_tech['RSI'].iloc[-1]
        if rsi > 70:
            st.error(f"⚠️ 超买区 ({rsi:.1f})")
        elif rsi < 30:
            st.success(f"🟢 超卖区 ({rsi:.1f})")
        else:
            st.info(f"▬ 正常区间 ({rsi:.1f})")
    
    # 布林带
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df_tech.index, y=df_tech['BB_Upper'], name='上轨', line=dict(color='red', width=1)))
    fig_bb.add_trace(go.Scatter(x=df_tech.index, y=df_tech['BB_Middle'], name='中轨', line=dict(color='yellow', width=1)))
    fig_bb.add_trace(go.Scatter(x=df_tech.index, y=df_tech['BB_Lower'], name='下轨', line=dict(color='green', width=1)))
    fig_bb.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'], name='收盘价', line=dict(color='white', width=1), fill='tonexty', fillcolor='rgba(255,255,255,0.1)'))
    fig_bb.update_layout(title='布林带', template='plotly_dark', height=300)
    st.plotly_chart(fig_bb, use_container_width=True)

# ==================== 缠论分析 ====================
if show_chan:
    st.markdown("---")
    st.header("🀄 缠论分析")
    
    def find_fractals(df):
        """寻找分型（顶分型/底分型）"""
        fractals = {'top': [], 'bottom': []}
        
        for i in range(2, len(df) - 2):
            # 顶分型
            if df['High'].iloc[i-2] < df['High'].iloc[i-1] > df['High'].iloc[i] < df['High'].iloc[i+1] > df['High'].iloc[i+2]:
                fractals['top'].append((df.index[i], df['High'].iloc[i]))
            
            # 底分型
            if df['Low'].iloc[i-2] > df['Low'].iloc[i-1] < df['Low'].iloc[i] > df['Low'].iloc[i+1] < df['Low'].iloc[i+2]:
                fractals['bottom'].append((df.index[i], df['Low'].iloc[i]))
        
        return fractals
    
    fractals = find_fractals(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 分型信号")
        top_count = len(fractals['top'])
        bottom_count = len(fractals['bottom'])
        
        st.info(f"顶分型数量: {top_count}")
        st.success(f"底分型数量: {bottom_count}")
        
        if top_count > bottom_count:
            st.warning("⚠️ 顶分型多于底分型，注意回调风险")
        elif bottom_count > top_count:
            st.success("🟢 底分型多于顶分型，可能有机会")
    
    with col2:
        st.markdown("#### 缠论走势判断")
        recent_high = df['High'].tail(20).max()
        recent_low = df['Low'].tail(20).min()
        current = df['Close'].iloc[-1]
        
        position = (current - recent_low) / (recent_high - recent_low) * 100 if recent_high > recent_low else 50
        
        st.progress(min(position / 100, 1.0))
        st.caption(f"当前价格在近期区间中位置: {position:.1f}%")
        
        if position > 80:
            st.error("⚠️ 接近区间上沿，注意风险")
        elif position < 20:
            st.success("🟢 接近区间下沿，关注机会")
        else:
            st.info("▬ 区间震荡中")
    
    # 缠论K线图
    fig_chan = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K线'
    )])
    
    if fractals['top']:
        top_x, top_y = zip(*fractals['top'][-10:])
        fig_chan.add_trace(go.Scatter(
            x=top_x, y=top_y, mode='markers',
            marker=dict(symbol='triangle-down', size=12, color='red'),
            name='顶分型'
        ))
    
    if fractals['bottom']:
        bottom_x, bottom_y = zip(*fractals['bottom'][-10:])
        fig_chan.add_trace(go.Scatter(
            x=bottom_x, y=bottom_y, mode='markers',
            marker=dict(symbol='triangle-up', size=12, color='green'),
            name='底分型'
        ))
    
    fig_chan.update_layout(title='缠论分型标注', template='plotly_dark', height=400)
    st.plotly_chart(fig_chan, use_container_width=True)
    
    st.caption("💡 缠论说明：顶分型是上涨趋势结束的信号，底分型是下跌趋势结束的信号")

# ==================== 韦科夫量价分析 ====================
if show_wyckoff:
    st.markdown("---")
    st.header("📊 韦科夫（Wyckoff）量价分析")
    
    df_wyckoff = df.copy()
    df_wyckoff['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
    df_wyckoff['VWAP'] = (df_wyckoff['TypicalPrice'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    df_wyckoff['VolumeChange'] = df['Volume'].pct_change() * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 趋势判断")
        current_vwap = df_wyckoff['VWAP'].iloc[-1]
        if current_price > current_vwap:
            st.success("▲ 价格在VWAP上方 - 上升趋势")
        else:
            st.error("▼ 价格在VWAP下方 - 下降趋势")
        
        avg_volume = df['Volume'].tail(20).mean()
        current_volume = df['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        st.info(f"成交量比率: {volume_ratio:.2f}x")
        if volume_ratio > 1.5:
            st.warning("⚠️ 放量 - 可能突破或反转")
        elif volume_ratio < 0.5:
            st.info("▬ 缩量 - 观望为主")
    
    with col2:
        st.markdown("#### 关键信号")
        recent_low = df['Low'].tail(5).min()
        yesterday_low = df['Low'].iloc[-2]
        
        if current_price > yesterday_low * 1.02:
            st.success("🟢 弹簧信号 - 可能有支撑")
        else:
            st.info("▬ 无明显弹簧信号")
        
        if current_price > df['High'].tail(5).max() and volume_ratio > 1.3:
            st.error("⚠️ UTAD信号 - 可能冲高回落")
    
    fig_vwap = go.Figure()
    fig_vwap.add_trace(go.Scatter(x=df_wyckoff.index, y=df_wyckoff['Close'], name='收盘价', line=dict(color='white', width=1)))
    fig_vwap.add_trace(go.Scatter(x=df_wyckoff.index, y=df_wyckoff['VWAP'], name='VWAP', line=dict(color='yellow', width=2)))
    fig_vwap.update_layout(title='价格 vs VWAP', template='plotly_dark', height=300)
    st.plotly_chart(fig_vwap, use_container_width=True)
    
    colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
    fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量')])
    fig_vol.update_layout(title='成交量分析', template='plotly_dark', height=250)
    st.plotly_chart(fig_vol, use_container_width=True)
    
    st.caption("💡 韦科夫原理：关注价格与成交量的关系，识别吸筹/派发阶段")

# ==================== 基本面分析 ====================
if show_fundamental:
    st.markdown("---")
    st.header("💰 基本面分析")
    
    if info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pe_ratio = info.get('forwardPE', info.get('trailingPE', 'N/A'))
            st.metric("市盈率 (PE)", f"{pe_ratio}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
        
        with col2:
            pb_ratio = info.get('priceToBook', 'N/A')
            st.metric("市净率 (PB)", f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio)
        
        with col3:
            market_cap = info.get('marketCap', 'N/A')
            if isinstance(market_cap, (int, float)):
                if market_cap > 1e12:
                    st.metric("市值", f"${market_cap/1e12:.2f}T")
                elif market_cap > 1e9:
                    st.metric("市值", f"${market_cap/1e9:.2f}B")
                else:
                    st.metric("市值", f"${market_cap/1e6:.2f}M")
            else:
                st.metric("市值", market_cap)
        
        with col4:
            dividend = info.get('dividendYield', 0)
            if dividend:
                st.metric("股息率", f"{dividend*100:.2f}%")
            else:
                st.metric("股息率", "N/A")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("52周最高", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")
        with col2:
            st.metric("52周最低", f"${info.get('fiftyTwoWeekLow', 'N/A')}")
        with col3:
            st.metric("总营收", f"${info.get('totalRevenue', 'N/A')}")
        with col4:
            st.metric("ROE", f"{info.get('returnOnEquity', 'N/A')}")
    else:
        st.warning("⚠️ 无法获取基本面数据")

# ==================== 估值分析 ====================
if show_valuation:
    st.markdown("---")
    st.header("🎯 估值分析")
    
    if info:
        pe = info.get('forwardPE') or info.get('trailingPE')
        eps = info.get('epsTrailingTwelveMonths')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 相对估值")
            if pe and eps:
                growth = info.get('earningsGrowth', 0) or 0
                if isinstance(growth, (int, float)):
                    dcf_price = eps * (1 + growth) * (1.02 / (0.10 - 0.02))
                    st.success(f"📊 DCF估值: ${dcf_price:.2f}")
                    
                    if pe < 15:
                        st.success("🟢 PE偏低，可能被低估")
                    elif pe > 30:
                        st.error("🔴 PE偏高，可能被高估")
                    else:
                        st.info("▬ PE合理区间")
            else:
                st.warning("数据不足")
        
        with col2:
            st.markdown("#### 价格位置")
            high52 = info.get('fiftyTwoWeekHigh', current_price)
            low52 = info.get('fiftyTwoWeekLow', current_price)
            
            if high52 and low52:
                price_position = (current_price - low52) / (high52 - low52) * 100
                st.progress(price_position / 100)
                st.caption(f"当前价格在52周区间的位置: {price_position:.1f}%")
                
                if price_position > 80:
                    st.error("⚠️ 接近52周高点，注意风险")
                elif price_position < 20:
                    st.success("🟢 接近52周低点，关注机会")

# ==================== 综合建议 ====================
st.markdown("---")
st.header("💡 综合分析建议")

signals = []

ma5 = df_tech['MA5'].iloc[-1]
ma20 = df_tech['MA20'].iloc[-1]
signals.append(("均线", "多头" if ma5 > ma20 else "空头", "green" if ma5 > ma20 else "red"))

macd = df_tech['MACD'].iloc[-1]
signal_val = df_tech['Signal'].iloc[-1]
signals.append(("MACD", "金叉" if macd > signal_val else "死叉", "green" if macd > signal_val else "red"))

rsi = df_tech['RSI'].iloc[-1]
if rsi > 70:
    signals.append(("RSI", "超买", "red"))
elif rsi < 30:
    signals.append(("RSI", "超卖", "green"))
else:
    signals.append(("RSI", "中性", "yellow"))

top_count = len(fractals['top'])
bottom_count = len(fractals['bottom'])
if bottom_count > top_count:
    signals.append(("缠论", "底分型", "green"))
elif top_count > bottom_count:
    signals.append(("缠论", "顶分型", "red"))
else:
    signals.append(("缠论", "中性", "yellow"))

cols = st.columns(len(signals))
for i, (name, status, color) in enumerate(signals):
    with cols[i]:
        if color == "green":
            st.success(f"**{name}**: {status}")
        elif color == "red":
            st.error(f"**{name}**: {status}")
        else:
            st.warning(f"**{name}**: {status}")

green_count = sum(1 for _, _, c in signals if c == "green")
red_count = sum(1 for _, _, c in signals if c == "red")

st.markdown("### 📋 总体判断")
if green_count > red_count:
    st.success("🟢 综合信号偏多，建议关注买入机会")
elif red_count > green_count:
    st.error("🔴 综合信号偏空，建议谨慎")
else:
    st.info("▬ 多空平衡，建议观望")

st.markdown("---")
st.caption(f"📊 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据来源: Yahoo Finance")
