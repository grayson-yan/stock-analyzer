"""
股票综合分析工具 - 详细分析版
包含：技术面详解、基本面详解、估值分析、风险评估、买卖建议
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="股票深度分析", page_icon="📈", layout="wide")

st.title("📈 股票深度分析报告")
st.markdown("---")

with st.sidebar:
    st.header("🔍 输入股票")
    
    # 自动识别A股代码
    symbol_input = st.text_input("股票代码", value="600519").upper().strip()
    
    # A股自动加后缀
    if symbol_input.isdigit() and len(symbol_input) == 6:
        if symbol_input.startswith('6'):
            symbol = symbol_input + ".SS"  # 上海
        elif symbol_input.startswith(('0', '3')):
            symbol = symbol_input + ".SZ"  # 深圳
        elif symbol_input.startswith('8'):
            symbol = symbol_input + ".BJ"  # 北京
        else:
            symbol = symbol_input
    elif '.' not in symbol_input:
        symbol = symbol_input  # 美股等直接用
    else:
        symbol = symbol_input
    
    st.caption(f"当前: {symbol}")
    
    st.markdown("---")
    period = st.selectbox("分析周期", ["1个月", "3个月", "6个月", "1年", "2年", "5年"], index=3)
    period_map = {"1个月":"1mo", "3个月":"3mo", "6个月":"6mo", "1年":"1y", "2年":"2y", "5年":"5y"}
    p = period_map[period]

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

df, info = get_data(symbol, p)

if df is None or len(df) == 0:
    st.error(f"❌ 无法获取 {symbol} 数据")
    st.info("试试: AAPL, MSFT, TSLA, NVDA, 0700.HK")
    st.stop()

# ==================== 价格数据 ====================
cp = float(df['Close'].iloc[-1])
pp = float(df['Close'].iloc[-2]) if len(df) > 1 else cp
chg = cp - pp
chg_pct = (chg / pp) * 100

st.header(f"📊 {symbol} 价格概览")
c1, c2, c3, c4 = st.columns(4)
c1.metric("当前价格", f"${cp:.2f}", f"{chg:+.2f} ({chg_pct:+.1f}%)")
c2.metric("最高价", f"${float(df['High'].max()):.2f}")
c3.metric("最低价", f"${float(df['Low'].min()):.2f}")
c4.metric("成交量", f"{float(df['Volume'].iloc[-1])/1e6:.2f}M")

# K线图
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
fig.update_layout(title=f'{symbol} K线走势', template='plotly_dark', height=350)
st.plotly_chart(fig, use_container_width=True)

# ==================== 技术分析 ====================
st.markdown("---")
st.header("📈 一、技术分析详解")

d = df.copy()
d['MA5'] = d['Close'].rolling(5).mean()
d['MA10'] = d['Close'].rolling(10).mean()
d['MA20'] = d['Close'].rolling(20).mean()
d['MA60'] = d['Close'].rolling(60).mean()

e1 = d['Close'].ewm(span=12).mean()
e2 = d['Close'].ewm(span=26).mean()
d['MACD'] = e1 - e2
d['Signal'] = d['MACD'].ewm(span=9).mean()
d['MACD_Hist'] = d['MACD'] - d['Signal']

dl = d['Close'].diff()
g = dl.where(dl>0,0).rolling(14).mean()
l = (-dl.where(dl<0,0)).rolling(14).mean()
d['RSI'] = 100 - (100/(1+g/l))

d['BB_Mid'] = d['Close'].rolling(20).mean()
d['BB_Std'] = d['Close'].rolling(20).std()
d['BB_Up'] = d['BB_Mid'] + 2*d['BB_Std']
d['BB_Down'] = d['BB_Mid'] - 2*d['BB_Std']

# 计算技术指标值
ma5 = float(d['MA5'].iloc[-1])
ma10 = float(d['MA10'].iloc[-1])
ma20 = float(d['MA20'].iloc[-1])
ma60 = float(d['MA60'].iloc[-1]) if len(d) > 60 else ma20
macd = float(d['MACD'].iloc[-1])
signal = float(d['Signal'].iloc[-1])
macd_hist = float(d['MACD_Hist'].iloc[-1])
rsi = float(d['RSI'].iloc[-1])
bb_up = float(d['BB_Up'].iloc[-1])
bb_mid = float(d['BB_Mid'].iloc[-1])
bb_down = float(d['BB_Down'].iloc[-1])

# 技术信号
tech_signals = []

# 均线分析
trend = "震荡"
if ma5 > ma10 > ma20:
    trend = "上涨趋势"
    tech_signals.append(("趋势", "🟢 上涨趋势", "5日均线>10日>20日，显示短期多头排列，股价处于上升通道"))
elif ma5 < ma10 < ma20:
    trend = "下跌趋势"
    tech_signals.append(("趋势", "🔴 下跌趋势", "均线空头排列，短期均线在长期均线下方，建议谨慎"))
else:
    tech_signals.append(("趋势", "🟡 震荡整理", "均线纠缠，方向不明确，建议观望"))

# MACD分析
if macd > signal and macd_hist > 0:
    macd_signal = "🟢 金叉"
    macd_reason = "MACD线上穿信号线且柱状图为正值，动能转强，看涨"
elif macd < signal and macd_hist < 0:
    macd_signal = "🔴 死叉"
    macd_reason = "MACD线下穿信号线且柱状图为负，动能走弱，注意风险"
else:
    macd_signal = "🟡 观望"
    macd_reason = "MACD在零轴附近震荡，方向不明"
tech_signals.append(("MACD", macd_signal, macd_reason))

# RSI分析
if rsi < 30:
    rsi_signal = "🟢 超卖"
    rsi_reason = f"RSI={rsi:.1f}，已超卖区域，可能存在反弹机会"
elif rsi > 70:
    rsi_signal = "🔴 超买"
    rsi_reason = f"RSI={rsi:.1f}，已超买区域，注意回调风险"
elif rsi >= 50:
    rsi_signal = "🟡 偏强"
    rsi_reason = f"RSI={rsi:.1f}，在50以上，偏多头市场"
else:
    rsi_signal = "🟡 偏弱"
    rsi_reason = f"RSI={rsi:.1f}，在50以下，偏空头市场"
tech_signals.append(("RSI", rsi_signal, rsi_reason))

# 布林带分析
if cp > bb_up:
    bb_signal = "🔴 突破上轨"
    bb_reason = f"价格突破布林带上轨，可能过热，注意回调"
elif cp < bb_down:
    bb_signal = "🟢 触及下轨"
    bb_reason = f"价格触及布林带下轨，可能超卖，存在反弹机会"
else:
    bb_signal = "🟡 区间内"
    bb_reason = f"价格在布林带区间内运行，正常波动"
tech_signals.append(("布林带", bb_signal, bb_reason))

# 显示技术分析
st.subheader("技术指标详解")
for name, signal, reason in tech_signals:
    if "🟢" in signal:
        st.success(f"**{name}**: {signal}")
    elif "🔴" in signal:
        st.error(f"**{name}**: {signal}")
    else:
        st.warning(f"**{name}**: {signal}")
    st.caption(f"💡 {reason}")

# 技术面总结
tech_buy = sum(1 for _,s,_ in tech_signals if "🟢" in s)
tech_sell = sum(1 for _,s,_ in tech_signals if "🔴" in s)

if tech_buy >= 3:
    tech_conclusion = "技术面**强烈看涨**"
elif tech_buy > tech_sell:
    tech_conclusion = "技术面**偏多**"
elif tech_sell > tech_buy:
    tech_conclusion = "技术面**偏空**"
else:
    tech_conclusion = "技术面**中性**"

st.markdown(f"### 📊 技术面结论: {tech_conclusion}")

# ==================== 基本面分析 ====================
st.markdown("---")
st.header("💰 二、基本面分析")

if info and isinstance(info, dict):
    pe = info.get('forwardPE') or info.get('trailingPE')
    pb = info.get('priceToBook')
    mc = info.get('marketCap')
    div = info.get('dividendYield')
    roe = info.get('returnOnEquity')
    rev = info.get('totalRevenue')
    profit = info.get('profitMargins')
    debt = info.get('debtToEquity')
    
    # 显示指标
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("市盈率PE", f"{pe:.1f}" if pe else "N/A")
    c2.metric("市净率PB", f"{pb:.1f}" if pb else "N/A")
    c3.metric("市值", f"${mc/1e9:.0f}B" if mc else "N/A")
    c4.metric("股息率", f"{div*100:.1f}%" if div else "N/A")
    
    # 基本面分析
    st.subheader("基本面指标解读")
    fund_signals = []
    
    if pe:
        if pe < 15:
            pe_signal = "🟢 低估"
            pe_reason = f"PE={pe:.1f}，低于15，属于价值区间，可能被低估"
        elif pe > 40:
            pe_signal = "🔴 高估"
            pe_reason = f"PE={pe:.1f}，高于40，估值偏高，注意风险"
        else:
            pe_signal = "🟡 合理"
            pe_reason = f"PE={pe:.1f}，在15-40之间，估值合理"
        fund_signals.append(("PE估值", pe_signal, pe_reason))
    
    if roe:
        if roe > 0.15:
            roe_signal = "🟢 高ROE"
            roe_reason = f"ROE={roe*100:.1f}%，高于15%，股东回报优秀"
        elif roe > 0.08:
            roe_signal = "🟡 中等ROE"
            roe_reason = f"ROE={roe*100:.1f}%，在8-15%，盈利正常"
        else:
            roe_signal = "🔴 低ROE"
            roe_reason = f"ROE={roe*100:.1f}%，低于8%，盈利较弱"
        fund_signals.append(("ROE", roe_signal, roe_reason))
    
    if div and div > 0.03:
        div_signal = "🟢 高股息"
        div_reason = f"股息率{div*100:.1f}%，高于3%，收益稳定"
        fund_signals.append(("股息", div_signal, div_reason))
    
    if debt and debt < 50:
        debt_signal = "🟢 低负债"
        debt_reason = f"负债率{debt:.1f}%，低于50%，财务健康"
    elif debt and debt > 100:
        debt_signal = "🔴 高负债"
        debt_reason = f"负债率{debt:.1f}%，高于100%，财务风险较大"
    else:
        debt_signal = "🟡 中等负债"
        debt_reason = f"负债率{debt:.1f}%，在合理范围"
    fund_signals.append(("负债", debt_signal, debt_reason))
    
    for name, signal, reason in fund_signals:
        if "🟢" in signal:
            st.success(f"**{name}**: {signal}")
        elif "🔴" in signal:
            st.error(f"**{name}**: {signal}")
        else:
            st.warning(f"**{name}**: {signal}")
        st.caption(f"💡 {reason}")
    
    # 业务描述
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    business = info.get('businessSummary', '暂无')
    
    st.subheader("公司概况")
    st.info(f"**行业**: {sector} | **板块**: {industry}")
    st.markdown(f"**业务简介**: {business[:300]}..." if len(business) > 300 else f"**业务简介**: {business}")
    
    fund_buy = sum(1 for _,s,_ in fund_signals if "🟢" in s)
    fund_sell = sum(1 for _,s,_ in fund_signals if "🔴" in s)
    
    if fund_buy >= 2:
        fund_conclusion = "基本面**良好**"
    elif fund_sell >= 2:
        fund_conclusion = "基本面**较弱**"
    else:
        fund_conclusion = "基本面**一般**"
    
    st.markdown(f"### 💰 基本面结论: {fund_conclusion}")

else:
    st.warning("⚠️ 基本面数据获取失败")

# ==================== 估值分析 ====================
st.markdown("---")
st.header("🎯 三、估值分析")

if info and isinstance(info, dict) and pe and cp > 0:
    eps = info.get('epsTrailingTwelveMonths')
    growth = info.get('earningsGrowth')
    
    # 简单DCF
    if eps and growth:
        dcf = eps * (1 + growth) * (1.02 / 0.08)
        upside = (dcf - cp) / cp * 100
        
        if upside > 20:
            val_signal = "🟢 严重低估"
            val_reason = f"DCF估值${dcf:.2f}，相对当前价格有{upside:.0f}%上涨空间"
        elif upside > 0:
            val_signal = "🟡 轻微低估"
            val_reason = f"DCF估值${dcf:.2f}，略微高估，有{upside:.0f}%上涨空间"
        else:
            val_signal = "🔴 高估"
            val_reason = f"DCF估值${dcf:.2f}，相对当前价格高估{abs(upside):.0f}%"
        
        st.success(f"**估值**: {val_signal}")
        st.caption(f"💡 {val_reason}")
        
        # 52周位置
        high52 = info.get('fiftyTwoWeekHigh')
        low52 = info.get('fiftyTwoWeekLow')
        if high52 and low52:
            pos = (cp - low52) / (high52 - low52) * 100
            if pos < 20:
                pos_signal = "🟢 低位"
                pos_reason = f"当前价格在52周区间的{pos:.0f}%位置，属于低位，有上涨空间"
            elif pos > 80:
                pos_signal = "🔴 高位"
                pos_reason = f"当前价格在52周区间的{pos:.0f}%位置，接近高点，注意回调风险"
            else:
                pos_signal = "🟡 中位"
                pos_reason = f"当前价格在52周区间的{pos:.0f}%位置，属于中间位置"
            
            st.warning(f"**价格位置**: {pos_signal}")
            st.caption(f"💡 {pos_reason}")

# ==================== 风险评估 ====================
st.markdown("---")
st.header("⚠️ 四、风险评估")

if info and isinstance(info, dict):
    beta = info.get('beta')
    high52 = info.get('fiftyTwoWeekHigh')
    low52 = info.get('fiftyTwoWeekLow')
    
    # 支撑位阻力位
    support = low52 if low52 else cp * 0.9
    resistance = high52 if high52 else cp * 1.1
    
    st.subheader("支撑与阻力")
    c1, c2 = st.columns(2)
    c1.success(f"**支撑位**: ${support:.2f}")
    c1.caption(f"💡 下跌至此位置可能获得支撑")
    c2.error(f"**阻力位**: ${resistance:.2f}")
    c2.caption(f"💡 上涨至此位置可能遇到阻力")
    
    # Beta风险
    if beta:
        if beta > 1.5:
            risk = "🔴 高风险"
            risk_reason = f"Beta={beta:.2f}，波动性高于市场1.5倍以上，适合激进型投资者"
        elif beta > 1:
            risk = "🟡 中等风险"
            risk_reason = f"Beta={beta:.2f}，波动性略高于市场"
        else:
            risk = "🟢 低风险"
            risk_reason = f"Beta={beta:.2f}，波动性低于市场，较稳健"
        
        st.subheader("波动风险")
        st.warning(f"**市场风险**: {risk}")
        st.caption(f"💡 {risk_reason}")

# ==================== 综合结论 ====================
st.markdown("---")
st.header("🎯 五、综合投资建议")

# 汇总所有信号
all_buy = tech_buy + (fund_buy if 'fund_buy' in dir() else 0)
all_sell = tech_sell + (fund_sell if 'fund_sell' in dir() else 0)

total_signals = 3 + len(fund_signals)
buy_score = all_buy / total_signals * 10
sell_score = all_sell / total_signals * 10

stars = min(10, max(1, int(buy_score * 2 + 5 - sell_score)))

st.markdown(f"### {'⭐'*stars}{'☆'*(10-stars)} **{stars}/10**")

if stars >= 8:
    st.success("""
    ## ✅ 强烈推荐买入
    
    **理由**:
    - 技术面显示明显多头信号
    - 基本面估值合理或偏低
    - 价格处于合理区间
    
    **建议**: 可以考虑分批建仓
    """)
elif stars >= 5:
    st.info("""
    ## ⚖️ 中性观望
    
    **理由**:
    - 多空信号均衡
    - 需要等待更明确的方向
    
    **建议**: 建议观望，等待更明确信号后再入场
    """)
else:
    st.error("""
    ## ⛔ 建议回避
    
    **理由**:
    - 技术面偏空
    - 估值可能偏高
    - 风险因素较多
    
    **建议**: 建议等待风险释放后再考虑
    """)

# 风险提示
st.markdown("---")
st.caption("⚠️ 免责声明: 本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
st.caption(f"📊 数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: Yahoo Finance")
