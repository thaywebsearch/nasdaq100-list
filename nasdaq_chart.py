"""
nasdaq_chart.py — Gráfico de linhas em tempo real do índice NASDAQ 100
Integra no app.py com:  from nasdaq_chart import render_nasdaq_chart

Funcionalidades:
  · Gráfico de linhas em tempo real via yfinance
  · Intervalos: 1m, 5m, 15m, 30m, 1h, 1d
  · Períodos: 1 dia, 5 dias, 1 mês, 3 meses, 6 meses, 1 ano
  · Preço atual, variação e volume em destaque
  · Auto-refresh configurável (10s, 30s, 60s)
  · Indicadores: média móvel 20 e 50 períodos
  · Estilo visual dark idêntico ao app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

try:
    import yfinance as yf
except ImportError:
    st.error("❌  Instala o yfinance:  pip install yfinance plotly")
    st.stop()


# ── CSS do chart ──────────────────────────────────────────────────────────────
CHART_CSS = """
<style>
/* ── Preço em destaque ── */
.price-header {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    padding: 1rem 0 0.5rem;
    flex-wrap: wrap;
}
.price-current {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #E8EDF5;
    line-height: 1;
}
.price-change-pos {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    color: #34C759;
    font-weight: 600;
}
.price-change-neg {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    color: #FF453A;
    font-weight: 600;
}
.price-label {
    font-size: 0.65rem;
    letter-spacing: 3px;
    color: #4A6FA5;
    text-transform: uppercase;
    font-family: 'Space Mono', monospace;
    padding-bottom: 6px;
}

/* ── Métricas secundárias ── */
.mini-metrics {
    display: flex;
    gap: 20px;
    padding: 0.5rem 0 1rem;
    flex-wrap: wrap;
}
.mini-metric {
    background: #0D1829;
    border: 1px solid #1A2E4A;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    min-width: 100px;
}
.mini-metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: #00D4FF;
}
.mini-metric-lbl {
    font-size: 0.6rem;
    letter-spacing: 2px;
    color: #4A6FA5;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── Controlos ── */
.stSelectbox > div > div {
    background-color: #0D1829 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 8px !important;
    color: #E8EDF5 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Refresh badge ── */
.refresh-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0D1829;
    border: 1px solid #1A2E4A;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-family: 'Space Mono', monospace;
    color: #4A6FA5;
    letter-spacing: 1px;
}
.dot-live {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34C759;
    animation: blink 1.2s infinite;
    display: inline-block;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.2; }
}
</style>
"""


# ── Fetch de dados ────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_nasdaq(periodo: str, intervalo: str) -> pd.DataFrame:
    """Descarrega dados do ^NDX via yfinance."""
    ticker = yf.Ticker("^NDX")
    df = ticker.history(period=periodo, interval=intervalo)
    df.index = pd.to_datetime(df.index)
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert("Europe/Lisbon")
    return df


def calcular_ma(df: pd.DataFrame, janela: int) -> pd.Series:
    return df["Close"].rolling(window=janela).mean()


def formatar_numero(n: float) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n:,.0f}"


# ── Componente principal ──────────────────────────────────────────────────────
def render_nasdaq_chart() -> None:
    st.markdown(CHART_CSS, unsafe_allow_html=True)

    # ── Controlos ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        periodo = st.selectbox(
            "Período",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            format_func=lambda x: {
                "1d": "1 Dia", "5d": "5 Dias", "1mo": "1 Mês",
                "3mo": "3 Meses", "6mo": "6 Meses", "1y": "1 Ano"
            }[x],
            index=0,
            label_visibility="collapsed",
            key="chart_periodo",
        )

    with col2:
        intervalo_map = {
            "1d":  ["1m", "5m", "15m", "30m"],
            "5d":  ["5m", "15m", "30m", "1h"],
            "1mo": ["30m", "1h", "1d"],
            "3mo": ["1h", "1d"],
            "6mo": ["1d"],
            "1y":  ["1d"],
        }
        opcoes_intervalo = intervalo_map[periodo]
        labels_intervalo = {
            "1m": "1 min", "5m": "5 min", "15m": "15 min",
            "30m": "30 min", "1h": "1 hora", "1d": "1 dia"
        }
        intervalo = st.selectbox(
            "Intervalo",
            options=opcoes_intervalo,
            format_func=lambda x: labels_intervalo[x],
            label_visibility="collapsed",
            key="chart_intervalo",
        )

    with col3:
        mostrar_ma = st.selectbox(
            "Médias móveis",
            options=["Nenhuma", "MA 20", "MA 50", "MA 20 + MA 50"],
            label_visibility="collapsed",
            key="chart_ma",
        )

    with col4:
        auto_refresh = st.selectbox(
            "Auto-refresh",
            options=[0, 10, 30, 60],
            format_func=lambda x: "Sem refresh" if x == 0 else f"Refresh {x}s",
            label_visibility="collapsed",
            key="chart_refresh",
        )

    # ── Fetch de dados ─────────────────────────────────────────────────────────
    with st.spinner("A carregar dados…"):
        try:
            df = fetch_nasdaq(periodo, intervalo)
        except Exception as e:
            st.error(f"Erro ao obter dados: {e}")
            return

    if df.empty:
        st.warning("Sem dados disponíveis para este período/intervalo.")
        return

    # ── Métricas ───────────────────────────────────────────────────────────────
    preco_atual  = df["Close"].iloc[-1]
    preco_abertura = df["Close"].iloc[0]
    variacao_pts = preco_atual - preco_abertura
    variacao_pct = (variacao_pts / preco_abertura) * 100
    maximo       = df["High"].max()
    minimo       = df["Low"].min()
    volume_total = df["Volume"].sum()
    positivo     = variacao_pts >= 0
    seta         = "▲" if positivo else "▼"
    cor_var      = "price-change-pos" if positivo else "price-change-neg"

    # ── Header de preço ────────────────────────────────────────────────────────
    col_preco, col_live = st.columns([4, 1])
    with col_preco:
        st.markdown(f"""
        <div class="price-header">
            <div>
                <div class="price-label">NASDAQ 100 · NDX</div>
                <div class="price-current">{preco_atual:,.2f}</div>
            </div>
            <div class="{cor_var}">{seta} {abs(variacao_pts):,.2f} ({abs(variacao_pct):.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    with col_live:
        agora = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"""
        <div style="padding-top:1.5rem;text-align:right">
            <div class="refresh-badge">
                <span class="dot-live"></span> LIVE · {agora}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Mini métricas ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="mini-metrics">
        <div class="mini-metric">
            <div class="mini-metric-val">{preco_abertura:,.2f}</div>
            <div class="mini-metric-lbl">Abertura</div>
        </div>
        <div class="mini-metric">
            <div class="mini-metric-val" style="color:#34C759">{maximo:,.2f}</div>
            <div class="mini-metric-lbl">Máximo</div>
        </div>
        <div class="mini-metric">
            <div class="mini-metric-val" style="color:#FF453A">{minimo:,.2f}</div>
            <div class="mini-metric-lbl">Mínimo</div>
        </div>
        <div class="mini-metric">
            <div class="mini-metric-val" style="color:#AEAEB2">{formatar_numero(volume_total)}</div>
            <div class="mini-metric-lbl">Volume</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Gráfico Plotly ─────────────────────────────────────────────────────────
    cor_linha = "#34C759" if positivo else "#FF453A"
    cor_fill  = "rgba(52,199,89,0.08)" if positivo else "rgba(255,69,58,0.08)"

    fig = go.Figure()

    # Linha principal
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="NASDAQ 100",
        line=dict(color=cor_linha, width=2),
        fill="tozeroy",
        fillcolor=cor_fill,
        hovertemplate=(
            "<b>%{x|%d/%m %H:%M}</b><br>"
            "Preço: <b>%{y:,.2f}</b><extra></extra>"
        ),
    ))

    # Médias móveis
    if "MA 20" in mostrar_ma:
        ma20 = calcular_ma(df, 20)
        fig.add_trace(go.Scatter(
            x=df.index, y=ma20,
            mode="lines", name="MA 20",
            line=dict(color="#00D4FF", width=1.2, dash="dot"),
            hovertemplate="MA20: <b>%{y:,.2f}</b><extra></extra>",
        ))

    if "MA 50" in mostrar_ma:
        ma50 = calcular_ma(df, 50)
        fig.add_trace(go.Scatter(
            x=df.index, y=ma50,
            mode="lines", name="MA 50",
            line=dict(color="#FF9500", width=1.2, dash="dot"),
            hovertemplate="MA50: <b>%{y:,.2f}</b><extra></extra>",
        ))

    # Layout dark
    fig.update_layout(
        paper_bgcolor="#060A12",
        plot_bgcolor="#060A12",
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
        showlegend="MA" in mostrar_ma,
        legend=dict(
            bgcolor="#0D1829",
            bordercolor="#1A2E4A",
            borderwidth=1,
            font=dict(color="#E8EDF5", size=11),
        ),
        xaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            showspikes=True,
            spikecolor="#4A6FA5",
            spikethickness=1,
            spikedash="dot",
        ),
        yaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            tickformat=",.0f",
            showspikes=True,
            spikecolor="#4A6FA5",
            spikethickness=1,
            spikedash="dot",
            side="right",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0D1829",
            bordercolor="#1A2E4A",
            font=dict(color="#E8EDF5", size=11, family="Space Mono"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
        "toImageButtonOptions": {
            "format": "png",
            "filename": f"nasdaq100_{datetime.now().strftime('%Y%m%d_%H%M')}",
        },
    })

    # ── Auto-refresh ───────────────────────────────────────────────────────────
    if auto_refresh > 0:
        st.caption(f"⟳  Próxima atualização em {auto_refresh}s")
        time.sleep(auto_refresh)
        st.cache_data.clear()
        st.rerun()
