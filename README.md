# 📊 Nasdaq‑100 Dataset — Composição Oficial + Market Cap

Dataset completo e atualizado com as 100 empresas que compõem o **Nasdaq‑100**, incluindo:

- rank  
- ticker  
- company  
- sector  
- weight  
- market_cap_usd (campo preparado para atualização automática via script)

Este repositório foi criado para análises financeiras, dashboards, automações, projetos Python e aplicações web.

---

## 📁 Estrutura do Repositório


---

## 🔗 GitHub Pages — Visualização Online

- **Tabela Nasdaq‑100 (Markdown)**  
  https://thaywebsearch.github.io/nasdaq100-list/nasdaq100-table

- **Market Cap (CSV)**  
  https://thaywebsearch.github.io/nasdaq100-list/nasdaq100_marketcap_052026.csv

---

## 🛠️ Como Utilizar

Este dataset pode ser usado em:

- Python (Pandas, NumPy)
- Excel / Google Sheets
- Power BI / Tableau
- Streamlit / Dash
- Projetos de análise de mercados
- Automação de dados financeiros

### Exemplo rápido em Python

```python
import pandas as pd

df = pd.read_csv("https://thaywebsearch.github.io/nasdaq100-list/nasdaq100-table.csv")
print(df.head())
