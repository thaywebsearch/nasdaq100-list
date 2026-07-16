"""
weight_chart.py — Gráfico de barras do peso (weight) das empresas do NASDAQ 100
Integra no app.py com:  from weight_chart import render_weight_chart

Funcionalidades:
  · Gráfico de barras horizontal por empresa
  · Filtro por Top N empresas (10, 25, 50, 100)
  · Filtro por setor
  · Cores por setor
  · Tooltip com ticker, empresa, setor e peso
  · Linha de média do índice
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ── Cores por setor ────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Technology":             "#00D4FF",
    "Communication Services": "#8B7FFF",
    "Consumer Discretionary": "#FF9500",
    "Consumer Staples":       "#34C759",
    "Health Care":            "#FF453A",
    "Industrials":            "#AEAEB2",
    "Utilities":              "#BF5AF2",
    "Energy":                 "#FF6B00",
    "Materials":              "#30D158",
}


def render_weight_chart(df: pd.DataFrame) -> None:

    # ── Controlos ──────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 2])

    with col1:
        top_n = st.selectbox(
            "Top empresas",
            options=[10, 25, 50, 100],
            format_func=lambda x: f"Top {x} empresas",
            index=0,
            label_visibility="collapsed",
            key="wc_topn",
        )
    with col2:
        setores = ["Todos os setores"] + sorted(df["sector"].unique().tolist())
        setor_sel = st.selectbox(
            "Setor",
            options=setores,
            label_visibility="collapsed",
            key="wc_setor",
        )

    # ── Filtrar dados ──────────────────────────────────────────────────────────
    df_plot = df.copy()
    if setor_sel != "Todos os setores":
        df_plot = df_plot[df_plot["sector"] == setor_sel]

    df_plot = df_plot.nsmallest(top_n, "rank")
    df_plot = df_plot.sort_values("weight", ascending=True)

    media = df_plot["weight"].mean()

    # ── Construir traces por setor (para legenda) ──────────────────────────────
    fig = go.Figure()

    for setor, grupo in df_plot.groupby("sector"):
        cor = SECTOR_COLORS.get(setor, "#E8EDF5")
        fig.add_trace(go.Bar(
            x=grupo["weight"],
            y=grupo["ticker"],
            orientation="h",
            name=setor,
            marker=dict(
                color=cor,
                opacity=0.85,
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            customdata=grupo[["company", "sector", "weight"]].values,
            hovertemplate=(
                "<b>%{y}</b> · %{customdata[0]}<br>"
                "Setor: %{customdata[1]}<br>"
                "Peso: <b>%{customdata[2]:.2f}%</b>"
                "<extra></extra>"
            ),
        ))

    # ── Linha de média ─────────────────────────────────────────────────────────
    fig.add_vline(
        x=media,
        line_dash="dot",
        line_color="#4A6FA5",
        line_width=1.2,
        annotation_text=f"  média {media:.2f}%",
        annotation_font=dict(color="#4A6FA5", size=10, family="Space Mono"),
        annotation_position="top",
    )

    # ── Layout ─────────────────────────────────────────────────────────────────
    altura = max(320, len(df_plot) * 22)

    fig.update_layout(
        paper_bgcolor="#060A12",
        plot_bgcolor="#060A12",
        margin=dict(l=0, r=20, t=10, b=20),
        height=altura,
        barmode="stack",
        showlegend=True,
        legend=dict(
            bgcolor="#0D1829",
            bordercolor="#1A2E4A",
            borderwidth=1,
            font=dict(color="#E8EDF5", size=10, family="Space Mono"),
            orientation="v",
            x=1.01,
            y=1,
        ),
        xaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#4A6FA5", size=9, family="Space Mono"),
            linecolor="#1A2E4A",
            ticksuffix="%",
            title=dict(
                text="Peso no índice (%)",
                font=dict(color="#4A6FA5", size=10, family="Space Mono"),
            ),
        ),
        yaxis=dict(
            gridcolor="#0D1829",
            tickcolor="#1A2E4A",
            tickfont=dict(color="#E8EDF5", size=10, family="Space Mono"),
            linecolor="#1A2E4A",
        ),
        hoverlabel=dict(
            bgcolor="#0D1829",
            bordercolor="#1A2E4A",
            font=dict(color="#E8EDF5", size=11, family="Space Mono"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": False,
    })

    # ── Resumo ─────────────────────────────────────────────────────────────────
    peso_total = df_plot["weight"].sum()
    st.caption(
        f"📊  {len(df_plot)} empresas · "
        f"Peso combinado: **{peso_total:.2f}%** · "
        f"Média: **{media:.2f}%**"
    )
