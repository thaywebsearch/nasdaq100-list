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
from plotly.subplots import make_subplots
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


@st.cache_data(ttl=30)
def fetch_indice(simbolo: str, periodo: str, intervalo: str) -> pd.DataFrame:
    """Descarrega dados de qualquer índice via yfinance."""
    ticker = yf.Ticker(simbolo)
    df = ticker.history(period=periodo, interval=intervalo)
    df.index = pd.to_datetime(df.index)
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert("Europe/Lisbon")
    return df


def calcular_ma(df: pd.DataFrame, janela: int) -> pd.Series:
    return df["Close"].rolling(window=janela).mean()


def calcular_bollinger(df: pd.DataFrame, janela: int = 20, desvios: float = 2.0):
    """Retorna (banda_superior, media, banda_inferior) de Bollinger."""
    media  = df["Close"].rolling(window=janela).mean()
    std    = df["Close"].rolling(window=janela).std()
    return media + desvios * std, media, media - desvios * std


def calcular_rsi(df: pd.DataFrame, janela: int = 14) -> pd.Series:
    """Calcula o RSI (Relative Strength Index) de N períodos."""
    delta  = df["Close"].diff()
    ganho  = delta.clip(lower=0)
    perda  = -delta.clip(upper=0)
    media_ganho = ganho.ewm(com=janela - 1, min_periods=janela).mean()
    media_perda = perda.ewm(com=janela - 1, min_periods=janela).mean()
    rs  = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return rsi


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
    col0, col1, col2, col3, col4 = st.columns([2, 2, 2, 2, 2, 2][:5])

    with col0:
        tipo_grafico = st.selectbox(
            "Tipo de gráfico",
            options=["Linha", "Candlestick"],
            format_func=lambda x: f"📈 {x}" if x == "Linha" else f"🕯️ {x}",
            label_visibility="collapsed",
            key="chart_tipo",
        )

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
        mostrar_bb = st.selectbox(
            "Bollinger",
            options=["Off", "BB 20", "BB 20 (2.5σ)"],
            format_func=lambda x: {
                "Off": "Bollinger: Off",
                "BB 20": "BB 20 (2σ)",
                "BB 20 (2.5σ)": "BB 20 (2.5σ)",
            }[x],
            label_visibility="collapsed",
            key="chart_bb",
        )

    col5, col6, col7, col8 = st.columns([2, 2, 2, 2])
    with col5:
        eixo_y = st.selectbox(
            "Eixo Y",
            options=["Preço", "Variação (%)"],
            format_func=lambda x: f"Eixo: {x}",
            label_visibility="collapsed",
            key="chart_eixo",
        )
    with col6:
        mostrar_rsi = st.selectbox(
            "RSI",
            options=["Off", "RSI 14", "RSI 9"],
            format_func=lambda x: f"RSI: {x}" if x != "Off" else "RSI: Off",
            label_visibility="collapsed",
            key="chart_rsi",
        )
    with col7:
        comparar_com = st.selectbox(
            "Comparar com",
            options=["Off", "S&P 500", "Dow Jones", "VIX"],
            format_func=lambda x: f"vs {x}" if x != "Off" else "Comparar: Off",
            label_visibility="collapsed",
            key="chart_comparar",
        )
    with col8:
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

    # ── Modo percentagem ──────────────────────────────────────────────────────
    preco_base = df["Close"].iloc[0]
    df = df.copy()
    df["Close_pct"]  = ((df["Close"]  - preco_base) / preco_base) * 100
    df["Open_pct"]   = ((df["Open"]   - preco_base) / preco_base) * 100
    df["High_pct"]   = ((df["High"]   - preco_base) / preco_base) * 100
    df["Low_pct"]    = ((df["Low"]    - preco_base) / preco_base) * 100
    usar_pct = eixo_y == "Variação (%)"

    col_close  = "Close_pct"  if usar_pct else "Close"
    col_open   = "Open_pct"   if usar_pct else "Open"
    col_high   = "High_pct"   if usar_pct else "High"
    col_low    = "Low_pct"    if usar_pct else "Low"

    # ── Fetch índice de comparação ─────────────────────────────────────────────
    simbolos_comparar = {
        "S&P 500":   "^GSPC",
        "Dow Jones": "^DJI",
        "VIX":       "^VIX",
    }
    df_comp = None
    tem_comp = comparar_com != "Off"
    if tem_comp:
        try:
            sim = simbolos_comparar[comparar_com]
            df_comp = fetch_indice(sim, periodo, intervalo)
            if not df_comp.empty:
                base_comp = df_comp["Close"].iloc[0]
                df_comp["Close_pct"] = ((df_comp["Close"] - base_comp) / base_comp) * 100
        except Exception:
            df_comp = None

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

    # ── Mini-métrica do índice de comparação ───────────────────────────────────
    if tem_comp and df_comp is not None and not df_comp.empty:
        comp_atual    = df_comp["Close"].iloc[-1]
        comp_base     = df_comp["Close"].iloc[0]
        comp_var_pct  = ((comp_atual - comp_base) / comp_base) * 100
        comp_positivo = comp_var_pct >= 0
        comp_cor      = "#34C759" if comp_positivo else "#FF453A"
        comp_seta     = "▲" if comp_positivo else "▼"
        st.markdown(f"""
        <div style="display:inline-flex;gap:16px;margin-bottom:0.5rem">
            <div class="mini-metric" style="border-color:#8B7FFF44">
                <div class="mini-metric-val" style="color:#8B7FFF">{comparar_com}</div>
                <div class="mini-metric-lbl">índice comparado</div>
            </div>
            <div class="mini-metric" style="border-color:{comp_cor}44">
                <div class="mini-metric-val" style="color:{comp_cor}">{comp_seta} {abs(comp_var_pct):.2f}%</div>
                <div class="mini-metric-lbl">variação período</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Gráfico Plotly ─────────────────────────────────────────────────────────
    cor_linha = "#34C759" if positivo else "#FF453A"
    cor_fill  = "rgba(52,199,89,0.08)" if positivo else "rgba(255,69,58,0.08)"

    # Sub-gráficos dinâmicos: preço + volume + RSI (opcional)
    tem_rsi = mostrar_rsi != "Off"
    if tem_rsi:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.60, 0.20, 0.20],
            vertical_spacing=0.03,
        )
    else:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.75, 0.25],
            vertical_spacing=0.03,
        )
    row_vol = 3 if tem_rsi else 2

    if tipo_grafico == "Linha":
        # ── Gráfico de linha ───────────────────────────────────────────────────
        sufixo = "%" if usar_pct else ""
        fmt    = ".2f" if usar_pct else ",.2f"
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col_close],
            mode="lines",
            name="NASDAQ 100",
            line=dict(color=cor_linha, width=2),
            fill="tozeroy",
            fillcolor=cor_fill,
            hovertemplate=(
                f"<b>%{{x|%d/%m %H:%M}}</b><br>"
                f"Fecho: <b>%{{y:{fmt}}}{sufixo}</b><extra></extra>"
            ),
        ), row=1, col=1)
    else:
        # ── Candlestick ────────────────────────────────────────────────────────
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df[col_open],
            high=df[col_high],
            low=df[col_low],
            close=df[col_close],
            name="NASDAQ 100",
            increasing=dict(
                line=dict(color="#34C759", width=1),
                fillcolor="rgba(52,199,89,0.75)",
            ),
            decreasing=dict(
                line=dict(color="#FF453A", width=1),
                fillcolor="rgba(255,69,58,0.75)",
            ),
            hovertext=[
                f"<b>{t.strftime('%d/%m %H:%M')}</b><br>"
                f"Abertura: <b>{o:,.2f}</b><br>"
                f"Máximo:   <b>{h:,.2f}</b><br>"
                f"Mínimo:   <b>{l:,.2f}</b><br>"
                f"Fecho:    <b>{c:,.2f}</b>"
                for t, o, h, l, c in zip(
                    df.index, df["Open"], df["High"], df["Low"], df["Close"]
                )
            ],
            hoverinfo="text",
        ), row=1, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False)

    # ── Linha de comparação (S&P 500 / Dow / VIX) ────────────────────────────
    if tem_comp and df_comp is not None and not df_comp.empty:
        y_comp = df_comp["Close_pct"] if usar_pct else df_comp["Close"]
        # Normalizar para começar no mesmo ponto do NASDAQ se em preço absoluto
        if not usar_pct:
            escala = df["Close"].iloc[0] / df_comp["Close"].iloc[0]
            y_comp = df_comp["Close"] * escala

        fig.add_trace(go.Scatter(
            x=df_comp.index,
            y=y_comp,
            mode="lines",
            name=comparar_com,
            line=dict(color="#8B7FFF", width=1.5, dash="dot"),
            opacity=0.8,
            hovertemplate=(
                f"<b>{comparar_com}</b><br>"
                "%{x|%d/%m %H:%M}<br>"
                "Valor: <b>%{y:,.2f}</b><extra></extra>"
            ),
        ), row=1, col=1)

    # Médias móveis
    if "MA 20" in mostrar_ma:
        ma20 = calcular_ma(df.assign(Close=df[col_close]), 20)
        fig.add_trace(go.Scatter(
            x=df.index, y=ma20,
            mode="lines", name="MA 20",
            line=dict(color="#00D4FF", width=1.2, dash="dot"),
            hovertemplate="MA20: <b>%{y:,.2f}</b><extra></extra>",
        ), row=1, col=1)

    if "MA 50" in mostrar_ma:
        ma50 = calcular_ma(df.assign(Close=df[col_close]), 50)
        fig.add_trace(go.Scatter(
            x=df.index, y=ma50,
            mode="lines", name="MA 50",
            line=dict(color="#FF9500", width=1.2, dash="dot"),
            hovertemplate="MA50: <b>%{y:,.2f}</b><extra></extra>",
        ), row=1, col=1)

    # ── Bandas de Bollinger ────────────────────────────────────────────────────
    if mostrar_bb != "Off":
        desvios = 2.5 if "2.5" in mostrar_bb else 2.0
        bb_sup, bb_med, bb_inf = calcular_bollinger(df.assign(Close=df[col_close]), janela=20, desvios=desvios)

        # Banda superior
        fig.add_trace(go.Scatter(
            x=df.index, y=bb_sup,
            mode="lines", name=f"BB Sup ({desvios}σ)",
            line=dict(color="rgba(191,90,242,0.6)", width=1, dash="dash"),
            hovertemplate=f"BB Sup: <b>%{{y:,.2f}}</b><extra></extra>",
        ), row=1, col=1)
        # Área preenchida entre bandas
        fig.add_trace(go.Scatter(
            x=df.index, y=bb_inf,
            mode="lines", name=f"BB Inf ({desvios}σ)",
            line=dict(color="rgba(191,90,242,0.6)", width=1, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(191,90,242,0.06)",
            hovertemplate=f"BB Inf: <b>%{{y:,.2f}}</b><extra></extra>",
        ), row=1, col=1)
        # Linha central (média 20)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb_med,
            mode="lines", name="BB Média (20)",
            line=dict(color="rgba(191,90,242,0.4)", width=1, dash="dot"),
            hovertemplate="BB Média: <b>%{y:,.2f}</b><extra></extra>",
        ), row=1, col=1)

    # ── Sub-gráfico de Volume (row 2) ────────────────────────────────────────
    cores_volume = [
        "rgba(52,199,89,0.6)" if c >= o else "rgba(255,69,58,0.6)"
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(go.Bar(
        x=df.index,
        y=df["Volume"],
        name="Volume",
        marker=dict(color=cores_volume, line=dict(width=0)),
        hovertemplate="Volume: <b>%{y:,.0f}</b><extra></extra>",
    ), row=row_vol, col=1)

    # ── RSI (row 3 se ativo) ──────────────────────────────────────────────────
    if tem_rsi:
        janela_rsi = 9 if "9" in mostrar_rsi else 14
        rsi = calcular_rsi(df, janela=janela_rsi)

        # Linha RSI
        fig.add_trace(go.Scatter(
            x=df.index, y=rsi,
            mode="lines",
            name=f"RSI {janela_rsi}",
            line=dict(color="#FF9500", width=1.5),
            hovertemplate=f"RSI {janela_rsi}: <b>%{{y:.1f}}</b><extra></extra>",
        ), row=3, col=1)

        # Zona sobre-compra (>70) — vermelho
        fig.add_hrect(
            y0=70, y1=100,
            fillcolor="rgba(255,69,58,0.07)",
            line_width=0,
            row=3, col=1,
        )
        # Zona sobre-venda (<30) — verde
        fig.add_hrect(
            y0=0, y1=30,
            fillcolor="rgba(52,199,89,0.07)",
            line_width=0,
            row=3, col=1,
        )
        # Linhas de referência 70 e 30
        for nivel, cor in [(70, "rgba(255,69,58,0.5)"), (50, "rgba(74,111,165,0.4)"), (30, "rgba(52,199,89,0.5)")]:
            fig.add_hline(
                y=nivel,
                line_dash="dot",
                line_color=cor,
                line_width=1,
                row=3, col=1,
            )

    # ── Anotações automáticas de Máximo e Mínimo ────────────────────────────
    y_col = col_close  # usar coluna correta (preço ou %)
    idx_max = df[y_col].idxmax()
    idx_min = df[y_col].idxmin()
    val_max = df[y_col][idx_max]
    val_min = df[y_col][idx_min]
    sufixo_anot = "%" if usar_pct else ""
    fmt_anot    = ".2f" if usar_pct else ",.2f"

    # Posição vertical das etiquetas: máx acima, mín abaixo
    pos_max = "above"  if val_max >= df[y_col].median() else "below"
    pos_min = "below"  if val_min <= df[y_col].median() else "above"

    fig.add_annotation(
        x=idx_max, y=val_max,
        text=f"▲ MÁX<br><b>{val_max:{fmt_anot}}{sufixo_anot}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor="#34C759",
        ax=0, ay=-38,
        bgcolor="#0D1829",
        bordercolor="#34C759",
        borderwidth=1,
        borderpad=5,
        font=dict(color="#34C759", size=10, family="Space Mono"),
        row=1, col=1,
    )

    fig.add_annotation(
        x=idx_min, y=val_min,
        text=f"▼ MÍN<br><b>{val_min:{fmt_anot}}{sufixo_anot}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor="#FF453A",
        ax=0, ay=38,
        bgcolor="#0D1829",
        bordercolor="#FF453A",
        borderwidth=1,
        borderpad=5,
        font=dict(color="#FF453A", size=10, family="Space Mono"),
        row=1, col=1,
    )

    # Layout dark com crosshair sincronizado
    fig.update_layout(
        paper_bgcolor="#060A12",
        plot_bgcolor="#060A12",
        margin=dict(l=0, r=0, t=10, b=0),
        height=580 if tem_rsi else 480,
        showlegend=("MA" in mostrar_ma or mostrar_bb != "Off" or tem_comp),
        legend=dict(
            bgcolor="#0D1829",
            bordercolor="#1A2E4A",
            borderwidth=1,
            font=dict(color="#E8EDF5", size=11),
        ),
        # ── Crosshair sincronizado em ambos os painéis ─────────────────────────
        hovermode="x",
        hoverdistance=50,
        spikedistance=1000,
        # Painel 1 — Preço
        xaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            showticklabels=False,   # esconder datas no painel superior
            showspikes=True,
            spikecolor="#E8EDF5",
            spikethickness=1,
            spikedash="solid",
            spikemode="across",
            spikesnap="cursor",
        ),
        yaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            tickformat=".2f" if usar_pct else ",.0f",
            ticksuffix="%" if usar_pct else "",
            showspikes=True,
            spikecolor="#E8EDF5",
            spikethickness=1,
            spikedash="solid",
            spikemode="across",
            spikesnap="cursor",
            side="right",
            **({"zeroline": True, "zerolinecolor": "#4A6FA5",
                "zerolinewidth": 1} if usar_pct else {}),
        ),
        # Painel 2 — Volume
        xaxis2=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            showticklabels=not tem_rsi,  # ocultar datas se RSI estiver ativo
            showspikes=True,
            spikecolor="#E8EDF5",
            spikethickness=1,
            spikedash="solid",
            spikemode="across",
            spikesnap="cursor",
        ),
        yaxis2=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=9, family="Space Mono"),
            linecolor="#1A2E4A",
            tickformat=".2s",
            side="right",
            title=dict(
                text="VOL",
                font=dict(color="#4A6FA5", size=9, family="Space Mono"),
            ),
        ),
        # Painel 3 — RSI (só existe se ativo)
        **({"xaxis3": dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
            showspikes=True,
            spikecolor="#E8EDF5",
            spikethickness=1,
            spikedash="solid",
            spikemode="across",
            spikesnap="cursor",
        ),
        "yaxis3": dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=9, family="Space Mono"),
            linecolor="#1A2E4A",
            range=[0, 100],
            tickvals=[0, 30, 50, 70, 100],
            side="right",
            title=dict(
                text="RSI",
                font=dict(color="#FF9500", size=9, family="Space Mono"),
            ),
        )} if tem_rsi else {}),
        hoverlabel=dict(
            bgcolor="#0D1829",
            bordercolor="#00D4FF",
            font=dict(color="#E8EDF5", size=12, family="Space Mono"),
            namelength=-1,
        ),
        xaxis_rangeslider_visible=False,
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
