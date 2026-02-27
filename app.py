"""
股票综合分析工具 - 精简稳定版
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="股票分析工具", page_icon="📈", layout="wide")

st.title("📈 股票综合分析工具")

with st.sidebar:
    st.header("🔍 股票搜索")
    symbol = st.text_input("输入股票代码", value="AAPL").upper().strip()
    
    st.markdown("---")
    st.header("📊 时间周期")
    timeframe = st.selectbox("选择周期", ["日线", "1周", "1月", "3月", "6月", "1年", "2年", "5年"], index=5)
    
    timeframe_map = {"日线":"1d", "1周":"5d", "1月":"1mo", "3月":"3mo", "6月":"6mo", "1年":"1y", "2年":"2y", "5年":"5y"}
    period = timeframe_map[timeframe]

@st.cache_data(ttl=300)
def get_data(sym, per):
    try:
        t = yf.Ticker(sym)
        df = t.history(period=per)
        info = {}
        try:
            info = t.info or {}
        except:
            pass
        return df, info
    except:
        return None, {}

df, info = get_data(symbol, period)

if df is None or len(df) == 0:
    st.error(f"❌ 无法获取 {symbol} 数据")
    st.stop()

cp = float(df['Close'].iloc[-1]) if pd.notna(df['Close'].iloc[-1]) else 0
pp = float(df['Close'].iloc[-2]) if len(df) > 1 and pd.notna(df['Close'].iloc[-2]) else cp
chg = cp - pp
chg_pct = (chg / pp) * 100 if pp != 0 else 0

st.header(f"📊 {symbol} 概览")
c1, c2, c3, c4 = st.columns(4)
c1.metric("价格", f"${cp:.2f}", f"{chg:+.2f} ({chg_pct:+.1f}%)")
c2.metric("最高", f"${float(df['High'].max()):.2f}")
c3.metric("最低", f"${float(df['Low'].min()):.2f}")
c4.metric("成交量", f"{float(df['Volume'].iloc[-1])/1e6:.1f}M")

st.subheader("📊 K线图")
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
fig.update_layout(template='plotly_dark', height=400)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.header("📈 技术分析")

d = df.copy()
d['MA5'] = d['Close'].rolling(5).mean()
d['MA20'] = d['Close'].rolling(20).mean()

e1 = d['Close'].ewm(span=12).mean()
e2 = d['Close'].ewm(span=26).mean()
d['MACD'] = e1 - e2
d['Signal'] = d['MACD'].ewm(span=9).mean()

dl = d['Close'].diff()
g = dl.where(dl>0,0).rolling(14).mean()
l = (-dl.where(dl<0,0)).rolling(14).mean()
d['RSI'] = 100 - (100/(1+g/l))

ma5 = float(d['MA5'].iloc[-1]) if pd.notna(d['MA5'].iloc[-1]) else 0
ma20 = float(d['MA20'].iloc[-1]) if pd.notna(d['MA20'].iloc[-1]) else 0
macd = float(d['MACD'].iloc[-1]) if pd.notna(d['MACD'].iloc[-1]) else 0
sig = float(d['Signal'].iloc[-1]) if pd.notna(d['Signal'].iloc[-1]) else 0
rsi = float(d['RSI'].iloc[-1]) if pd.notna(d['RSI'].iloc[-1]) else 50

signals = []
if ma5 > ma20: signals.append(("均线", "多头", "🟢"))
else: signals.append(("均线", "空头", "🔴"))

if macd > sig: signals.append(("MACD", "金叉", "🟢"))
else: signals.append(("MACD", "死叉", "🔴"))

if rsi < 30: signals.append(("RSI", "超卖", "🟢"))
elif rsi > 70: signals.append(("RSI", "超买", "🔴"))
else: signals.append(("RSI", "正常", "🟡"))

c1, c2 = st.columns([3,1])
with c1:
    f = go.Figure()
    f.add_trace(go.Scatter(x=d.index, y=d['MA5'], name='MA5', line=dict(color='yellow')))
    f.add_trace(go.Scatter(x=d.index, y=d['MA20'], name='MA20', line=dict(color='red')))
    f.add_trace(go.Scatter(x=d.index, y=d['Close'], name='价格', line=dict(color='white')))
    f.update_layout(template='plotly_dark', height=250)
    st.plotly_chart(f, use_container_width=True)
with c2:
    st.markdown("### 信号")
    for n, s, e in signals:
        st.write(f"{e} **{n}**: {s}")

st.markdown("---")
st.header("🀄 缠论分析")

fr = {'t':[], 'b':[]}
for i in range(2, len(df)-2):
    if df['High'].iloc[i-2] < df['High'].iloc[i-1] > df['High'].iloc[i] < df['High'].iloc[i+1] > df['High'].iloc[i+2]:
        fr['t'].append(i)
    if df['Low'].iloc[i-2] > df['Low'].iloc[i-1] < df['Low'].iloc[i] > df['Low'].iloc[i+1] < df['Low'].iloc[i+2]:
        fr['b'].append(i)

tc, bc = len(fr['t']), len(fr['b'])
if bc > tc: st.success(f"🟢 底分型多({bc}>{tc}) - 关注买入")
elif tc > bc: st.error(f"🔴 顶分型多({tc}>{bc}) - 注意风险")
else: st.info("▬ 分型均衡")

if info:
    st.markdown("---")
    st.header("💰 基本面")
    c1, c2, c3, c4 = st.columns(4)
    pe = info.get('forwardPE') or info.get('trailingPE')
    c1.metric("PE", f"{pe:.1f}" if pe else "N/A")
    pb = info.get('priceToBook')
    c2.metric("PB", f"{pb:.1f}" if pb else "N/A")
    mc = info.get('marketCap')
    c3.metric("市值", f"${mc/1e9:.0f}B" if mc else "N/A")
    dy = info.get('dividendYield')
    c4.metric("股息", f"{dy*100:.1f}%" if dy else "N/A")

st.markdown("---")
st.header("⭐ 综合评级")

buy_c = sum(1 for _,_,e in signals if e=="🟢")
sell_c = sum(1 for _,_,e in signals if e=="🔴")
stars = min(10, max(1, buy_c*3 + (3-buy_c-sell_c)*1))

st.markdown(f"### {'⭐'*stars}{'☆'*(10-stars)} **{stars}/10**")

if stars >= 7: st.success("⭐ 推荐买入")
elif stars >= 4: st.info("⭐ 观望")
else: st.error("⭐ 建议回避")

st.caption(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 仅供参考")
