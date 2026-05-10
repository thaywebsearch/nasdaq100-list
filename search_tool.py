"""
search_tool.py — Ferramenta de busca avançada NASDAQ 100
Integra no app.py com:  from search_tool import render_search_tool

Funcionalidades:
  · Pesquisa em tempo real por ticker, empresa e setor
  · Filtros combinados: setor, peso mínimo/máximo, market cap
  · Ordenação por qualquer coluna (asc/desc)
  · Destaque dos termos pesquisados nos resultados
  · Exportação dos resultados filtrados para CSV
  · Painel de estatísticas dinâmicas dos resultados
  · Histórico das últimas pesquisas na sessão
"""

import streamlit as st
import pandas as pd
import io
import re


# ── CSS da search tool ────────────────────────────────────────────────────────
SEARCH_CSS = """
<style>
/* ── Search bar ── */
.search-wrapper {
    position: relative;
    margin-bottom: 1rem;
}
.search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: #4A6FA5;
    font-size: 16px;
    pointer-events: none;
    z-index: 10;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 24px;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #0D1829;
    border: 1px solid #1A2E4A;
    border-radius: 10px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.stat-item { text-align: center; }
.stat-val {
    font-family: 'Space Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    color: #00D4FF;
}
.stat-lbl {
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: #4A6FA5;
    text-transform: uppercase;
}
.stat-divider {
    width: 1px;
    height: 32px;
    background: #1A2E4A;
}

/* ── Badges de setor ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
}

/* ── Histórico ── */
.history-chip {
    display: inline-block;
    padding: 3px 10px;
    background: #0D1829;
    border: 1px solid #1A2E4A;
    border-radius: 20px;
    font-size: 12px;
    color: #4A6FA5;
    margin: 2px;
    cursor: pointer;
    font-family: 'Space Mono', monospace;
}
.history-chip:hover { border-color: #00D4FF; color: #00D4FF; }

/* ── Resultado highlight ── */
.highlight {
    background: #00D4FF22;
    color: #00D4FF;
    border-radius: 3px;
    padding: 0 2px;
    font-weight: 700;
}

/* ── Export button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0057FF, #00D4FF) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    padding: 0.5rem 1.2rem !important;
    transition: opacity 0.2s !important;
}
.stDownloadButton > button:hover { opacity: 0.85 !important; }

/* ── Filtros avançados ── */
.filtros-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    color: #4A6FA5;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Sem resultados ── */
.no-results {
    text-align: center;
    padding: 3rem 1rem;
    color: #4A6FA5;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 2px;
}
</style>
"""

# ── Cores por setor ────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Technology":              {"bg": "#0D2340", "color": "#00D4FF"},
    "Communication Services":  {"bg": "#1A1040", "color": "#8B7FFF"},
    "Consumer Discretionary":  {"bg": "#2D1A00", "color": "#FF9500"},
    "Consumer Staples":        {"bg": "#0A2A10", "color": "#34C759"},
    "Health Care":             {"bg": "#2D0A0A", "color": "#FF453A"},
    "Industrials":             {"bg": "#1A1A1A", "color": "#AEAEB2"},
    "Utilities":               {"bg": "#1A1030", "color": "#BF5AF2"},
    "Energy":                  {"bg": "#2D1A00", "color": "#FF6B00"},
    "Materials":               {"bg": "#0A2020", "color": "#30D158"},
}


def _badge(sector: str) -> str:
    sc = SECTOR_COLORS.get(sector, {"bg": "#1A2E4A", "color": "#E8EDF5"})
    return (
        f'<span class="badge" style="background:{sc["bg"]};color:{sc["color"]}">'
        f'{sector}</span>'
    )


def _highlight(text: str, term: str) -> str:
    """Destaca o termo pesquisado no texto."""
    if not term or len(term) < 2:
        return text
    try:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        return pattern.sub(
            lambda m: f'<span class="highlight">{m.group()}</span>', str(text)
        )
    except re.error:
        return text


def _parse_market_cap(val: str) -> float:
    """Converte '3.21T' → 3210 (em B) para comparação."""
    val = str(val).strip().upper()
    try:
        if val.endswith("T"):
            return float(val[:-1]) * 1000
        if val.endswith("B"):
            return float(val[:-1])
        if val.endswith("M"):
            return float(val[:-1]) / 1000
        return float(val)
    except ValueError:
        return 0.0


def _to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# ── Componente principal ──────────────────────────────────────────────────────
def render_search_tool(df: pd.DataFrame) -> None:
    """
    Renderiza a ferramenta de busca avançada.
    Recebe o DataFrame completo do NASDAQ 100.
    """
    st.markdown(SEARCH_CSS, unsafe_allow_html=True)

    # ── Inicializar histórico na sessão ───────────────────────────────────────
    if "search_history" not in st.session_state:
        st.session_state.search_history = []

    # ── Linha 1: Search bar principal ─────────────────────────────────────────
    col_input, col_clear = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            label="search_main",
            placeholder="🔍  Pesquisar por empresa, ticker ou setor…",
            label_visibility="collapsed",
            key="search_query",
        )
    with col_clear:
        if st.button("✕ Limpar", use_container_width=True, key="btn_clear"):
            st.session_state.search_query = ""
            st.rerun()

    # ── Histórico de pesquisas ─────────────────────────────────────────────────
    if st.session_state.search_history:
        st.markdown(
            "<span style='font-size:11px;color:#4A6FA5;letter-spacing:2px;"
            "text-transform:uppercase;font-family:Space Mono,monospace'>"
            "PESQUISAS RECENTES &nbsp;</span>" +
            " ".join(
                f'<span class="history-chip">⏱ {h}</span>'
                for h in reversed(st.session_state.search_history[-5:])
            ),
            unsafe_allow_html=True,
        )

    # ── Filtros avançados (expansível) ────────────────────────────────────────
    with st.expander("⚙️  Filtros avançados", expanded=False):
        st.markdown('<div class="filtros-header">Setor</div>', unsafe_allow_html=True)
        setores = ["Todos"] + sorted(df["sector"].unique().tolist())
        setor_sel = st.selectbox("Setor", setores, label_visibility="collapsed", key="f_sector")

        st.markdown('<div class="filtros-header" style="margin-top:1rem">Peso no índice (%)</div>', unsafe_allow_html=True)
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            peso_min = st.number_input("Mínimo", min_value=0.0, max_value=15.0,
                                       value=0.0, step=0.1, format="%.1f",
                                       key="f_peso_min", label_visibility="collapsed")
        with col_w2:
            peso_max = st.number_input("Máximo", min_value=0.0, max_value=15.0,
                                       value=15.0, step=0.1, format="%.1f",
                                       key="f_peso_max", label_visibility="collapsed")

        st.markdown('<div class="filtros-header" style="margin-top:1rem">Market Cap mínimo</div>', unsafe_allow_html=True)
        cap_opcoes = {
            "Todos": 0,
            "> 100B": 100,
            "> 500B": 500,
            "> 1T (1000B)": 1000,
            "> 2T (2000B)": 2000,
        }
        cap_sel = st.selectbox("Market Cap mínimo", list(cap_opcoes.keys()),
                               label_visibility="collapsed", key="f_cap")

        st.markdown('<div class="filtros-header" style="margin-top:1rem">Ordenar por</div>', unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sort_col = st.selectbox(
                "Coluna",
                ["rank", "ticker", "company", "sector", "weight", "market_cap_usd"],
                format_func=lambda x: {
                    "rank": "# Posição", "ticker": "Ticker",
                    "company": "Empresa", "sector": "Setor",
                    "weight": "Peso (%)", "market_cap_usd": "Market Cap"
                }.get(x, x),
                label_visibility="collapsed",
                key="f_sort_col",
            )
        with col_s2:
            sort_dir = st.selectbox(
                "Direção", ["Ascendente", "Descendente"],
                label_visibility="collapsed", key="f_sort_dir"
            )

    # ── Aplicar filtros ───────────────────────────────────────────────────────
    resultado = df.copy()
    resultado["_cap_b"] = resultado["market_cap_usd"].apply(_parse_market_cap)

    # Texto
    q = query.strip()
    if q and len(q) >= 1:
        mask = (
            resultado["ticker"].str.contains(q, case=False, na=False) |
            resultado["company"].str.contains(q, case=False, na=False) |
            resultado["sector"].str.contains(q, case=False, na=False)
        )
        resultado = resultado[mask]
        # Guardar no histórico
        if q and (not st.session_state.search_history or st.session_state.search_history[-1] != q):
            st.session_state.search_history.append(q)
            if len(st.session_state.search_history) > 10:
                st.session_state.search_history.pop(0)

    # Setor
    if setor_sel != "Todos":
        resultado = resultado[resultado["sector"] == setor_sel]

    # Peso
    resultado = resultado[
        (resultado["weight"] >= peso_min) &
        (resultado["weight"] <= peso_max)
    ]

    # Market cap
    cap_min_b = cap_opcoes[cap_sel]
    if cap_min_b > 0:
        resultado = resultado[resultado["_cap_b"] >= cap_min_b]

    # Ordenação
    ascending = sort_dir == "Ascendente"
    if sort_col == "market_cap_usd":
        resultado = resultado.sort_values("_cap_b", ascending=ascending)
    else:
        resultado = resultado.sort_values(sort_col, ascending=ascending)

    resultado = resultado.drop(columns=["_cap_b"])

    # ── Barra de estatísticas dinâmicas ───────────────────────────────────────
    n = len(resultado)
    peso_total = resultado["weight"].sum()
    n_setores = resultado["sector"].nunique()
    top_ticker = resultado.iloc[0]["ticker"] if n > 0 else "—"

    st.markdown(f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-val">{n}</div>
            <div class="stat-lbl">Resultados</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-val">{peso_total:.2f}%</div>
            <div class="stat-lbl">Peso total</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-val">{n_setores}</div>
            <div class="stat-lbl">Setores</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-val">{top_ticker}</div>
            <div class="stat-lbl">Top resultado</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Resultados ─────────────────────────────────────────────────────────────
    if n == 0:
        st.markdown("""
        <div class="no-results">
            ∅ &nbsp; NENHUM RESULTADO ENCONTRADO<br>
            <span style="font-size:11px;opacity:0.5">Tenta outro termo ou ajusta os filtros</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Tabela com highlight e badges
    html_rows = ""
    for _, row in resultado.iterrows():
        ticker_hl  = _highlight(row["ticker"],  q)
        company_hl = _highlight(row["company"], q)
        badge      = _badge(row["sector"])
        html_rows += f"""
        <tr style="border-bottom:1px solid #1A2E4A">
          <td style="padding:10px 12px;color:#4A6FA5;font-family:Space Mono,monospace;font-size:12px">{int(row['rank'])}</td>
          <td style="padding:10px 12px;font-family:Space Mono,monospace;font-weight:700;color:#00D4FF;font-size:13px">{ticker_hl}</td>
          <td style="padding:10px 12px;font-size:13px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{company_hl}</td>
          <td style="padding:10px 12px">{badge}</td>
          <td style="padding:10px 12px;font-family:Space Mono,monospace;font-size:12px;color:#4A6FA5;text-align:right">{row['weight']:.2f}%</td>
          <td style="padding:10px 12px;font-family:Space Mono,monospace;font-size:12px;color:#34C759;text-align:right">{row['market_cap_usd']}</td>
        </tr>"""

    st.markdown(f"""
    <div style="border:1px solid #1A2E4A;border-radius:12px;overflow:hidden;max-height:480px;overflow-y:auto">
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#0D1829;position:sticky;top:0;z-index:1">
            <th style="padding:10px 12px;text-align:left;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">#</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">Ticker</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">Empresa</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">Setor</th>
            <th style="padding:10px 12px;text-align:right;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">Peso</th>
            <th style="padding:10px 12px;text-align:right;font-size:11px;letter-spacing:2px;color:#4A6FA5;font-family:Space Mono,monospace;font-weight:500;text-transform:uppercase">Market Cap</th>
          </tr>
        </thead>
        <tbody style="background:#060A12">{html_rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Exportar CSV ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_exp, col_info = st.columns([1, 3])
    with col_exp:
        st.download_button(
            label="⬇  Exportar resultados CSV",
            data=_to_csv(resultado),
            file_name=f"nasdaq100_filtrado_{pd.Timestamp.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_info:
        st.caption(
            f"📋  {n} empresa{'s' if n != 1 else ''} · "
            f"{n_setores} setor{'es' if n_setores != 1 else ''} · "
            f"Peso combinado: **{peso_total:.2f}%**"
        )
