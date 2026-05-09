"""
Atualiza automaticamente o Market Cap das 100 empresas do NASDAQ100.
Fonte de dados: Yahoo Finance (via yfinance) — gratuito, sem API key.

Requisitos:
    pip install yfinance pandas

Uso:
    python atualizar_market_cap.py
    python atualizar_market_cap.py --input outra_tabela.csv --output resultado.csv
    
"""

import argparse
import time
import csv
import io
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("❌  Instala o yfinance primeiro:  pip install yfinance pandas")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("❌  Instala o pandas primeiro:  pip install pandas")
    sys.exit(1)


# ── Dados embutidos (CSV original) ──────────────────────────────────────────
DADOS_CSV = """rank,ticker,company,sector,weight,market_cap_usd
1,NVDA,NVIDIA Corporation,Technology,13.31,-
2,AAPL,Apple Inc.,Technology,11.57,-
3,MSFT,Microsoft Corporation,Technology,8.55,-
4,AMZN,Amazon.com Inc.,Consumer Discretionary,7.07,-
5,GOOGL,Alphabet Inc. Class A,Communication Services,5.75,-
6,GOOG,Alphabet Inc. Class C,Communication Services,5.33,-
7,AVGO,Broadcom Inc.,Technology,4.60,-
8,META,Meta Platforms Inc. Class A,Communication Services,4.58,-
9,TSLA,Tesla Inc.,Consumer Discretionary,4.44,-
10,WMT,Walmart Inc.,Consumer Staples,3.06,-
11,ASML,ASML Holding N.V.,Technology,1.65,-
12,COST,Costco Wholesale Corporation,Consumer Staples,1.37,-
13,MU,Micron Technology Inc.,Technology,1.30,-
14,NFLX,Netflix Inc.,Communication Services,1.25,-
15,PLTR,Palantir Technologies Inc. Class A,Technology,1.09,-
16,AMD,Advanced Micro Devices Inc.,Technology,1.07,-
17,CSCO,Cisco Systems Inc.,Technology,0.97,-
18,AMAT,Applied Materials Inc.,Technology,0.88,-
19,LRCX,Lam Research Corporation,Technology,0.86,-
20,INTC,Intel Corporation,Technology,0.76,-
21,LIN,Linde plc,Materials,0.71,-
22,TMUS,T-Mobile US Inc.,Communication Services,0.69,-
23,PEP,PepsiCo Inc.,Consumer Staples,0.65,-
24,KLAC,KLA Corporation,Technology,0.62,-
25,AMGN,Amgen Inc.,Health Care,0.59,-
26,TXN,Texas Instruments Incorporated,Technology,0.56,-
27,GILD,Gilead Sciences Inc.,Health Care,0.54,-
28,ISRG,Intuitive Surgical Inc.,Health Care,0.51,-
29,ARM,Arm Holdings plc ADR,Technology,0.50,-
30,ADI,Analog Devices Inc.,Technology,0.49,-
31,SHOP,Shopify Inc. Class A,Consumer Discretionary,0.48,-
32,PDD,PDD Holdings Inc. ADR,Consumer Discretionary,0.45,-
33,HON,Honeywell International Inc.,Industrials,0.45,-
34,QCOM,QUALCOMM Incorporated,Technology,0.43,-
35,BKNG,Booking Holdings Inc.,Consumer Discretionary,0.42,-
36,APP,AppLovin Corporation Class A,Technology,0.41,-
37,PANW,Palo Alto Networks Inc.,Technology,0.40,-
38,INTU,Intuit Inc.,Technology,0.36,-
39,VRTX,Vertex Pharmaceuticals Incorporated,Health Care,0.36,-
40,SBUX,Starbucks Corporation,Consumer Discretionary,0.32,-
41,WDC,Western Digital Corporation,Technology,0.32,-
42,CEG,Constellation Energy Corporation,Utilities,0.31,-
43,CMCSA,Comcast Corporation Class A,Communication Services,0.31,-
44,CRWD,CrowdStrike Holdings Inc. Class A,Technology,0.31,-
45,ADBE,Adobe Inc.,Technology,0.30,-
46,STX,Seagate Technology Holdings plc,Technology,0.30,-
47,MRVL,Marvell Technology Inc.,Technology,0.29,-
48,MAR,Marriott International Inc. Class A,Consumer Discretionary,0.27,-
49,MELI,MercadoLibre Inc.,Consumer Discretionary,0.27,-
50,REGN,Regeneron Pharmaceuticals Inc.,Health Care,0.25,-
51,ADP,Automatic Data Processing Inc.,Technology,0.25,-
52,CDNS,Cadence Design Systems Inc.,Technology,0.24,-
53,ORLY,O'Reilly Automotive Inc.,Consumer Discretionary,0.24,-
54,CSX,CSX Corporation,Industrials,0.24,-
55,SNPS,Synopsys Inc.,Technology,0.24,-
56,ABNB,Airbnb Inc. Class A,Consumer Discretionary,0.24,-
57,MDLZ,Mondelez International Inc. Class A,Consumer Staples,0.23,-
58,MNST,Monster Beverage Corporation,Consumer Staples,0.22,-
59,ROST,Ross Stores Inc.,Consumer Discretionary,0.22,-
60,AEP,American Electric Power Company Inc.,Utilities,0.22,-
61,WBD,Warner Bros. Discovery Inc. Series A,Communication Services,0.22,-
62,CTAS,Cintas Corporation,Industrials,0.21,-
63,DASH,DoorDash Inc. Class A,Consumer Discretionary,0.20,-
64,PCAR,PACCAR Inc.,Industrials,0.19,-
65,FTNT,Fortinet Inc.,Technology,0.19,-
66,BKR,Baker Hughes Company Class A,Energy,0.18,-
67,MPWR,Monolithic Power Systems Inc.,Technology,0.17,-
68,FANG,Diamondback Energy Inc.,Energy,0.17,-
69,FAST,Fastenal Company,Industrials,0.17,-
70,EA,Electronic Arts Inc.,Communication Services,0.16,-
71,ADSK,Autodesk Inc.,Technology,0.16,-
72,NXPI,NXP Semiconductors N.V.,Technology,0.15,-
73,EXC,Exelon Corporation,Utilities,0.15,-
74,XEL,Xcel Energy Inc.,Utilities,0.15,-
75,FER,Ferrovial SE,Utilities,0.15,-
76,IDXX,IDEXX Laboratories Inc.,Health Care,0.14,-
77,ALNY,Alnylam Pharmaceuticals Inc.,Health Care,0.14,-
78,MSTR,Strategy Inc.,Technology,0.13,-
79,DDOG,Datadog Inc. Class A,Technology,0.13,-
80,ODFL,Old Dominion Freight Line Inc.,Industrials,0.13,-
81,PYPL,PayPal Holdings Inc.,Technology,0.13,-
82,CCEP,Coca-Cola Europacific Partners plc,Consumer Staples,0.13,-
83,TRI,Thomson Reuters Corporation,Technology,0.12,-
84,TTWO,Take-Two Interactive Software Inc.,Communication Services,0.11,-
85,ROP,Roper Technologies Inc.,Industrials,0.11,-
86,MCHP,Microchip Technology Incorporated,Technology,0.11,-
87,INSM,Insmed Incorporated,Health Care,0.11,-
88,KDP,Keurig Dr Pepper Inc.,Consumer Staples,0.11,-
89,AXON,Axon Enterprise Inc.,Industrials,0.11,-
90,WDAY,Workday Inc. Class A,Technology,0.10,-
91,PAYX,Paychex Inc.,Technology,0.10,-
92,GEHC,GE HealthCare Technologies Inc.,Health Care,0.10,-
93,CPRT,Copart Inc.,Industrials,0.10,-
94,CTSH,Cognizant Technology Solutions Corporation Class A,Technology,0.09,-
95,CHTR,Charter Communications Inc. Class A,Communication Services,0.08,-
96,KHC,Kraft Heinz Company,Consumer Staples,0.08,-
97,VRSK,Verisk Analytics Inc.,Technology,0.08,-
98,DXCM,DexCom Inc.,Health Care,0.08,-
99,ZS,Zscaler Inc. Class A,Technology,0.07,-
100,TEAM,Atlassian Corporation Class A,Technology,0.06,-
"""


# ── Utilitários ──────────────────────────────────────────────────────────────

def formatar_market_cap(valor: float) -> str:
    """Converte valor numérico em string legível (ex: 3.21T, 452.3B)."""
    if valor >= 1e12:
        return f"{valor / 1e12:.2f}T"
    elif valor >= 1e9:
        return f"{valor / 1e9:.1f}B"
    elif valor >= 1e6:
        return f"{valor / 1e6:.1f}M"
    return f"{valor:.0f}"


def obter_market_cap(ticker: str, pausa: float = 0.3) -> tuple[str, float | None]:
    """
    Obtém o market cap de um ticker via Yahoo Finance.
    Retorna (ticker, valor_em_usd | None).
    """
    try:
        info = yf.Ticker(ticker).info
        cap = info.get("marketCap")
        time.sleep(pausa)  # evitar rate-limiting
        return ticker, cap
    except Exception as e:
        print(f"  ⚠️  Erro ao obter {ticker}: {e}")
        return ticker, None


# ── Lógica principal ─────────────────────────────────────────────────────────

def carregar_dataframe(caminho_csv: str | None) -> pd.DataFrame:
    if caminho_csv and Path(caminho_csv).exists():
        print(f"📂  A carregar ficheiro: {caminho_csv}")
        return pd.read_csv(caminho_csv)
    else:
        print("📋  A usar dados embutidos no script.")
        return pd.read_csv(io.StringIO(DADOS_CSV))


def atualizar_market_caps(df: pd.DataFrame, pausa: float = 0.3) -> pd.DataFrame:
    tickers = df["ticker"].tolist()
    total = len(tickers)
    caps: dict[str, float | None] = {}

    print(f"\n🔄  A obter market caps de {total} empresas via Yahoo Finance...\n")

    for i, ticker in enumerate(tickers, 1):
        _, cap = obter_market_cap(ticker, pausa)
        caps[ticker] = cap

        estado = formatar_market_cap(cap) + " USD" if cap else "N/D"
        barra = "█" * int(i / total * 30) + "░" * (30 - int(i / total * 30))
        print(f"  [{barra}] {i:>3}/{total}  {ticker:<6}  {estado}", end="\r")

    print()  # nova linha após a barra de progresso
    df = df.copy()
    df["market_cap_usd"] = df["ticker"].map(
        lambda t: formatar_market_cap(caps[t]) if caps.get(t) else "-"
    )
    df["market_cap_raw"] = df["ticker"].map(lambda t: caps.get(t) or 0)
    return df


def guardar_resultado(df: pd.DataFrame, caminho_saida: str) -> None:
    colunas_saida = ["rank", "ticker", "company", "sector", "weight", "market_cap_usd"]
    df[colunas_saida].to_csv(caminho_saida, index=False)
    print(f"\n✅  Ficheiro guardado em: {caminho_saida}")


def mostrar_resumo(df: pd.DataFrame) -> None:
    df_sorted = df.dropna(subset=["market_cap_raw"]).sort_values("market_cap_raw", ascending=False)
    total_cap = df["market_cap_raw"].sum()

    print("\n" + "=" * 58)
    print("  TOP 10 por Market Cap (atual)")
    print("=" * 58)
    print(f"  {'#':<4} {'Ticker':<7} {'Empresa':<28} {'Market Cap':>10}")
    print("-" * 58)
    for _, row in df_sorted.head(10).iterrows():
        cap_str = formatar_market_cap(row["market_cap_raw"]) if row["market_cap_raw"] else "-"
        nome = row["company"][:27]
        print(f"  {int(row['rank']):<4} {row['ticker']:<7} {nome:<28} {cap_str + ' USD':>10}")
    print("=" * 58)
    print(f"  Market Cap total do índice: {formatar_market_cap(total_cap)} USD")
    atualizados = (df["market_cap_usd"] != "-").sum()
    print(f"  Empresas atualizadas: {atualizados}/{len(df)}")
    print(f"  Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 58)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Atualiza o Market Cap do NASDAQ 100 via Yahoo Finance."
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Caminho para o CSV de entrada (opcional; usa dados embutidos se omitido)."
    )
    parser.add_argument(
        "--output", "-o",
        default=f"nasdaq100_marketcap_{datetime.now().strftime('%Y%m%d')}.csv",
        help="Caminho para o CSV de saída (padrão: nasdaq100_marketcap_YYYYMMDD.csv)."
    )
    parser.add_argument(
        "--pausa", "-p",
        type=float,
        default=0.3,
        help="Pausa em segundos entre pedidos à API (padrão: 0.3)."
    )
    args = parser.parse_args()

    print("\n🚀  NASDAQ 100 — Atualizador de Market Cap")
    print("    Fonte: Yahoo Finance (yfinance)\n")

    df = carregar_dataframe(args.input)
    df = atualizar_market_caps(df, pausa=args.pausa)
    mostrar_resumo(df)
    guardar_resultado(df, args.output)


if __name__ == "__main__":
    main()
