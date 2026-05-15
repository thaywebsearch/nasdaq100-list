"""
NASDAQ 100 Dashboard — Streamlit App
Requisitos: pip install streamlit pandas

Uso:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="NASDAQ 100 Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #060A12;
    color: #E8EDF5;
}

/* ── Fundo geral ── */
.stApp {
    background: radial-gradient(ellipse at 20% 10%, #0D1F3C 0%, #060A12 60%);
}

/* ── Header animado ── */
.logo-container {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 2rem 0 0.5rem;
}

.logo-ring {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 3px solid transparent;
    background:
        linear-gradient(#060A12, #060A12) padding-box,
        conic-gradient(from 0deg, #00D4FF, #0057FF, #00D4FF) border-box;
    animation: spin 3s linear infinite;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

@keyframes spin {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.logo-text {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #00D4FF 0%, #0057FF 50%, #00D4FF 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
}

@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

.logo-sub {
    font-size: 0.75rem;
    letter-spacing: 4px;
    color: #4A6FA5;
    text-transform: uppercase;
    margin-top: -4px;
}

/* ── Métricas ── */
.metric-card {
    background: linear-gradient(135deg, #0D1829 0%, #0A1520 100%);
    border: 1px solid #1A2E4A;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    transition: border-color 0.3s;
}
.metric-card:hover { border-color: #00D4FF44; }
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00D4FF;
}
.metric-label {
    font-size: 0.72rem;
    letter-spacing: 3px;
    color: #4A6FA5;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── Tabela ── */
.stDataFrame { border-radius: 12px; overflow: hidden; }
thead tr th {
    background-color: #0D1829 !important;
    color: #4A6FA5 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
tbody tr:hover td { background-color: #0D1829 !important; }

/* ── Separador ── */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 4px;
    color: #4A6FA5;
    text-transform: uppercase;
    border-left: 3px solid #00D4FF;
    padding-left: 12px;
    margin: 2rem 0 1rem;
}

/* ── Search placeholder styling ── */
.stTextInput > div > div > input {
    background-color: #0D1829 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 8px !important;
    color: #E8EDF5 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 1px #00D4FF44 !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background-color: #0D1829 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 8px !important;
    color: #E8EDF5 !important;
}

/* ── Footer ── */
.footer {
    text-align: center;
    font-size: 0.7rem;
    letter-spacing: 2px;
    color: #1A2E4A;
    text-transform: uppercase;
    padding: 2rem 0 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── Dados ─────────────────────────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    dados = [
        (1,"NVDA","NVIDIA Corporation","Technology",13.31,"5.23T"),
        (2,"AAPL","Apple Inc.","Technology",11.57,"4.31T"),
        (3,"MSFT","Microsoft Corporation","Technology",8.55,"3.08T"),
        (4,"AMZN","Amazon.com Inc.","Consumer Discretionary",7.07,"2.93T"),
        (5,"GOOGL","Alphabet Inc. Class A","Communication Services",5.75,"4.86T"),
        (6,"GOOG","Alphabet Inc. Class C","Communication Services",5.33,"4.81T"),
        (7,"AVGO","Broadcom Inc.","Technology",4.60,"2.04T"),
        (8,"META","Meta Platforms Inc. Class A","Communication Services",4.58,"1.55T"),
        (9,"TSLA","Tesla Inc.","Consumer Discretionary",4.44,"1.61T"),
        (10,"WMT","Walmart Inc.","Consumer Staples",3.06,"1.04T"),
        (11,"ASML","ASML Holding N.V.","Technology",1.65,"613.6B"),
        (12,"COST","Costco Wholesale Corporation","Consumer Staples",1.37,"447.6B"),
        (13,"MU","Micron Technology Inc.","Technology",1.30,"842.2B"),
        (14,"NFLX","Netflix Inc.","Communication Services",1.25,"368.4B"),
        (15,"PLTR","Palantir Technologies Inc. Class A","Technology",1.09,"330.3B"),
        (16,"AMD","Advanced Micro Devices Inc.","Technology",1.07,"742.2B"),
        (17,"CSCO","Cisco Systems Inc.","Technology",0.97,"381.4B"),
        (18,"AMAT","Applied Materials Inc.","Technology",0.88,"345.6B"),
        (19,"LRCX","Lam Research Corporation","Technology",0.86,"367.7B"),
        (20,"INTC","Intel Corporation","Technology",0.76,"627.8B"),
        (21,"LIN","Linde plc","Materials",0.71,"228.0B"),
        (22,"TMUS","T-Mobile US Inc.","Communication Services",0.69,"209.5B"),
        (23,"PEP","PepsiCo Inc.","Consumer Staples",0.65,"211.4B"),
        (24,"KLAC","KLA Corporation","Technology",0.62,"244.2B"),
        (25,"AMGN","Amgen Inc.","Health Care",0.59,"179.1B"),
        (26,"TXN","Texas Instruments Incorporated","Technology",0.56,"261.9B"),
        (27,"GILD","Gilead Sciences Inc.","Health Care",0.54,"163.1B"),
        (28,"ISRG","Intuitive Surgical Inc.","Health Care",0.51,"159.4B"),
        (29,"ARM","Arm Holdings plc ADR","Technology",0.50,"226.9B"),
        (30,"ADI","Analog Devices Inc.","Technology",0.49,"203.3B"),
        (31,"SHOP","Shopify Inc. Class A","Consumer Discretionary",0.48,"143.3B"),
        (32,"PDD","PDD Holdings Inc. ADR","Consumer Discretionary",0.45,"140.6B"),
        (33,"HON","Honeywell International Inc.","Industrials",0.45,"135.0B"),
        (34,"QCOM","QUALCOMM Incorporated","Technology",0.43,"230.9B"),
        (35,"BKNG","Booking Holdings Inc.","Consumer Discretionary",0.42,"128.6B"),
        (36,"APP","AppLovin Corporation Class A","Technology",0.41,"157.4B"),
        (37,"PANW","Palo Alto Networks Inc.","Technology",0.40,"168.6B"),
        (38,"INTU","Intuit Inc.","Technology",0.36,"110.3B"),
        (39,"VRTX","Vertex Pharmaceuticals Incorporated","Health Care",0.36,"109.1B"),
        (40,"SBUX","Starbucks Corporation","Consumer Discretionary",0.32,"119.6B"),
        (41,"WDC","Western Digital Corporation","Technology",0.32,"165.4B"),
        (42,"CEG","Constellation Energy Corporation","Utilities",0.31,"110.0B"),
        (43,"CMCSA","Comcast Corporation Class A","Communication Services",0.31,"90.7B"),
        (44,"CRWD","CrowdStrike Holdings Inc. Class A","Technology",0.31,"134.3B"),
        (45,"ADBE","Adobe Inc.","Technology",0.30,"102.3B"),
        (46,"STX","Seagate Technology Holdings plc","Technology",0.30,"175.5B"),
        (47,"MRVL","Marvell Technology Inc.","Technology",0.29,"148.8B"),
        (48,"MAR","Marriott International Inc. Class A","Consumer Discretionary",0.27,"93.1B"),
        (49,"MELI","MercadoLibre Inc.","Consumer Discretionary",0.27,"82.8B"),
        (50,"REGN","Regeneron Pharmaceuticals Inc.","Health Care",0.25,"74.9B"),
        (51,"ADP","Automatic Data Processing Inc.","Technology",0.25,"85.1B"),
        (52,"CDNS","Cadence Design Systems Inc.","Technology",0.24,"100.0B"),
        (53,"ORLY","O'Reilly Automotive Inc.","Consumer Discretionary",0.24,"77.4B"),
        (54,"CSX","CSX Corporation","Industrials",0.24,"83.3B"),
        (55,"SNPS","Synopsys Inc.","Technology",0.24,"98.9B"),
        (56,"ABNB","Airbnb Inc. Class A","Consumer Discretionary",0.24,"84.1B"),
        (57,"MDLZ","Mondelez International Inc. Class A","Consumer Staples",0.23,"79.0B"),
        (58,"MNST","Monster Beverage Corporation","Consumer Staples",0.22,"84.4B"),
        (59,"ROST","Ross Stores Inc.","Consumer Discretionary",0.22,"73.0B"),
        (60,"AEP","American Electric Power Company Inc.","Utilities",0.22,"70.8B"),
        (61,"WBD","Warner Bros. Discovery Inc. Series A","Communication Services",0.22,"68.0B"),
        (62,"CTAS","Cintas Corporation","Industrials",0.21,"66.8B"),
        (63,"DASH","DoorDash Inc. Class A","Consumer Discretionary",0.20,"71.4B"),
        (64,"PCAR","PACCAR Inc.","Industrials",0.19,"60.2B"),
        (65,"FTNT","Fortinet Inc.","Technology",0.19,"83.5B"),
        (66,"BKR","Baker Hughes Company Class A","Energy",0.18,"63.4B"),
        (67,"MPWR","Monolithic Power Systems Inc.","Technology",0.17,"78.6B"),
        (68,"FANG","Diamondback Energy Inc.","Energy",0.17,"53.1B"),
        (69,"FAST","Fastenal Company","Industrials",0.17,"50.7B"),
        (70,"EA","Electronic Arts Inc.","Communication Services",0.16,"50.2B"),
        (71,"ADSK","Autodesk Inc.","Technology",0.16,"51.6B"),
        (72,"NXPI","NXP Semiconductors N.V.","Technology",0.15,"74.4B"),
        (73,"EXC","Exelon Corporation","Utilities",0.15,"44.9B"),
        (74,"XEL","Xcel Energy Inc.","Utilities",0.15,"49.6B"),
        (75,"FER","Ferrovial SE","Utilities",0.15,"50.5B"),
        (76,"IDXX","IDEXX Laboratories Inc.","Health Care",0.14,"44.2B"),
        (77,"ALNY","Alnylam Pharmaceuticals Inc.","Health Care",0.14,"39.4B"),
        (78,"MSTR","Strategy Inc.","Technology",0.13,"65.7B"),
        (79,"DDOG","Datadog Inc. Class A","Technology",0.13,"71.2B"),
        (80,"ODFL","Old Dominion Freight Line Inc.","Industrials",0.13,"41.2B"),
        (81,"PYPL","PayPal Holdings Inc.","Technology",0.13,"40.0B"),
        (82,"CCEP","Coca-Cola Europacific Partners plc","Consumer Staples",0.13,"41.9B"),
        (83,"TRI","Thomson Reuters Corporation","Technology",0.12,"40.6B"),
        (84,"TTWO","Take-Two Interactive Software Inc.","Communication Services",0.11,"40.8B"),
        (85,"ROP","Roper Technologies Inc.","Industrials",0.11,"34.6B"),
        (86,"MCHP","Microchip Technology Incorporated","Technology",0.11,"53.6B"),
        (87,"INSM","Insmed Incorporated","Health Care",0.11,"22.0B"),
        (88,"KDP","Keurig Dr Pepper Inc.","Consumer Staples",0.11,"39.2B"),
        (89,"AXON","Axon Enterprise Inc.","Industrials",0.11,"32.5B"),
        (90,"WDAY","Workday Inc. Class A","Technology",0.10,"31.9B"),
        (91,"PAYX","Paychex Inc.","Technology",0.10,"33.7B"),
        (92,"GEHC","GE HealthCare Technologies Inc.","Health Care",0.10,"28.9B"),
        (93,"CPRT","Copart Inc.","Industrials",0.10,"32.7B"),
        (94,"CTSH","Cognizant Technology Solutions Corporation Class A","Technology",0.09,"24.4B"),
        (95,"CHTR","Charter Communications Inc. Class A","Communication Services",0.08,"21.9B"),
        (96,"KHC","Kraft Heinz Company","Consumer Staples",0.08,"28.4B"),
        (97,"VRSK","Verisk Analytics Inc.","Technology",0.08,"22.5B"),
        (98,"DXCM","DexCom Inc.","Health Care",0.08,"23.4B"),
        (99,"ZS","Zscaler Inc. Class A","Technology",0.07,"24.5B"),
        (100,"TEAM","Atlassian Corporation Class A","Technology",0.06,"23.2B"),
    ]
    return pd.DataFrame(dados, columns=["rank","ticker","company","sector","weight","market_cap_usd"])


df = carregar_dados()


# ── LOGO animado ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="logo-container">
    <div class="logo-ring">📈</div>
    <div>
        <div class="logo-text">NASDAQ 100</div>
        <div class="logo-sub">Market Intelligence Dashboard</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ── Métricas de topo ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">100</div>
        <div class="metric-label">Empresas</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">9</div>
        <div class="metric-label">Setores</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">56.4%</div>
        <div class="metric-label">Peso Technology</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">5.23T</div>
        <div class="metric-label">Maior Market Cap</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── SECÇÃO 1: Search Tool avançada ───────────────────────────────────────────
from search_tool import render_search_tool

st.markdown('<div class="section-title">🔍 Search Tool</div>', unsafe_allow_html=True)
render_search_tool(df)


# ── SECÇÃO 2: Gráfico em tempo real do NASDAQ ────────────────────────────────
from nasdaq_chart import render_nasdaq_chart

st.markdown('<div class="section-title">📈 Índice NASDAQ 100 — Tempo Real</div>', unsafe_allow_html=True)
render_nasdaq_chart()


# ── Distribuição por setor ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗂️ Peso por Setor</div>', unsafe_allow_html=True)

df_setor = df.groupby("sector")["weight"].sum().sort_values(ascending=False).reset_index()
df_setor.columns = ["Setor", "Peso total (%)"]

st.bar_chart(df_setor.set_index("Setor"), color="#0057FF", use_container_width=True, height=280)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    NASDAQ 100 Dashboard · Dados via Yahoo Finance · Atualizado automaticamente
</div>
""", unsafe_allow_html=True)
