import json
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt

# Încarcă JSON
with open("history.json") as f:
    data = json.load(f)

# Normalizează timestamp-urile în timezone-aware UTC
entries = [
    {
        **e,
        "ts": datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    }
    for e in data
]

# Filtrare după delta de timp
def filter_since(delta):
    cutoff = datetime.now(timezone.utc) - delta
    return [e for e in entries if e["ts"] >= cutoff]

# Grafic pentru diverse perioade
for name, delta in [("1h", timedelta(hours=1)),
                    ("24h", timedelta(days=1)),
                    ("7d", timedelta(days=7))]:
    subset = filter_since(delta)
    times = [e["ts"] for e in subset]
    tokens = [
        e.get("usage", {}).get("total_token_count", 0)
        for e in subset
    ]
    plt.figure()
    plt.plot(times, tokens, marker='o')
    plt.title(f"Tokens used over last {name}")
    plt.xlabel("Time")
    plt.ylabel("Total tokens")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
