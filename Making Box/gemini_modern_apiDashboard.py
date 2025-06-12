#streamlit run gemini_modern_apiDashboard.py

import json
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ——— Încarcă datele din history.json ———
with open("history.json", encoding="utf-8") as f:
    data = json.load(f)

# Convertim datele în dataframe
records = []
for e in data:
    timestamp = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    tokens = e.get("usage", {}).get("total_token_count", 0)
    records.append({"timestamp": timestamp, "total_token_count": tokens})

df = pd.DataFrame(records)
df.sort_values("timestamp", inplace=True)

# ——— Interfața Streamlit ———
st.title("💎 Gemini API Usage Dashboard")

# Selectare perioadă dinamică
options = {
    "Ultima oră": timedelta(hours=1),
    "Ultimele 24h": timedelta(days=1),
    "Ultimele 7 zile": timedelta(days=7),
    "Toate": None
}
interval = st.selectbox("Perioada de afișare", list(options.keys()))

# Filtrare după perioada selectată
if options[interval]:
    cutoff = datetime.now(timezone.utc) - options[interval]
    df_filtered = df[df["timestamp"] >= cutoff]
else:
    df_filtered = df

# Grafic
fig, ax = plt.subplots()
ax.plot(df_filtered["timestamp"], df_filtered["total_token_count"], marker='o', linestyle='-')
ax.set_title(f"Token usage ({interval})")
ax.set_xlabel("Timp")
ax.set_ylabel("Total Tokens")
plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)
st.write(df_filtered)
