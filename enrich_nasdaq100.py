"""
enrich_nasdaq100.py
--------------------
Lê o CSV original do NASDAQ-100 e gera uma versão enriquecida com:
  - market_cap_numeric : valor numérico em USD (float)
  - market_cap_billions: valor em biliões (B) arredondado a 1 decimal
  - cap_category       : Mega / Large / Mid Cap
  - weight_cumulative  : peso acumulado no índice (%)
  - index_concentration: Top 10 / Top 25 / Rest
  - snapshot_date      : data de referência do snapshot
"""

import pandas as pd

# ── 1. Carregar o CSV original ────────────────────────────────────────────────
INPUT  = "nasdaq100_marketcap_052026.csv"
OUTPUT = "nasdaq100_marketcap_052026_enriched.csv"

df = pd.read_csv(INPUT)
print(f"✅ Carregado: {len(df)} empresas, {df.columns.tolist()}")


# ── 2. Converter market_cap_usd (string) → float em USD ──────────────────────
def parse_market_cap(value: str) -> float:
    """
    Converte strings como '5.47T' ou '609.6B' para float em USD.
    T = Trillion (10^12) | B = Billion (10^9)
    """
    value = str(value).strip()
    if value.endswith("T"):
        return float(value[:-1]) * 1_000_000_000_000
    elif value.endswith("B"):
        return float(value[:-1]) * 1_000_000_000
    else:
        return float(value)  # já é número

df["market_cap_numeric"] = df["market_cap_usd"].apply(parse_market_cap)

# Versão em biliões (mais legível em gráficos)
df["market_cap_billions"] = (df["market_cap_numeric"] / 1_000_000_000).round(1)

print("✅ market_cap convertido para float")


# ── 3. Classificar por tamanho de capitalização ───────────────────────────────
def cap_category(market_cap_usd: float) -> str:
    """
    Classificação padrão de mercado:
      Mega Cap  : > $200B
      Large Cap : $10B – $200B
      Mid Cap   : < $10B  (improvável no NASDAQ-100 mas seguro incluir)
    """
    if market_cap_usd >= 200_000_000_000:
        return "Mega Cap"
    elif market_cap_usd >= 10_000_000_000:
        return "Large Cap"
    else:
        return "Mid Cap"

df["cap_category"] = df["market_cap_numeric"].apply(cap_category)

print("✅ cap_category calculado")


# ── 4. Peso acumulado no índice ───────────────────────────────────────────────
# O dataset já está ordenado por rank, então basta cumsum() direto
df["weight_cumulative"] = df["weight"].cumsum().round(2)

print("✅ weight_cumulative calculado")


# ── 5. Concentração do índice ─────────────────────────────────────────────────
def index_concentration(rank: int) -> str:
    """Agrupa empresas por tier de influência no índice."""
    if rank <= 10:
        return "Top 10"
    elif rank <= 25:
        return "Top 11–25"
    else:
        return "Rest (26–100)"

df["index_concentration"] = df["rank"].apply(index_concentration)

print("✅ index_concentration calculado")


# ── 6. Data de referência do snapshot ────────────────────────────────────────
df["snapshot_date"] = "2026-05-01"

print("✅ snapshot_date adicionado")


# ── 7. Guardar CSV enriquecido ────────────────────────────────────────────────
df.to_csv(OUTPUT, index=False)

print(f"\n🎉 Ficheiro gerado: {OUTPUT}")
print(f"   Colunas finais: {df.columns.tolist()}")
print(f"\nPré-visualização das primeiras 5 linhas:")
print(df.head().to_string())
