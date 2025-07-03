import streamlit as st

# --- PAGINA PRINCIPALĂ ---
st.set_page_config(page_title="Proiect Brat Robotic - Antrenare AI", layout="wide")

st.title("🤖 Proiect Brat Robotic - Generare și Clasificare Imagini AI")
st.markdown(
    "Bine ai venit în aplicația dedicată proiectului tău de braț robotic! 🎉  "
    "Folosește secțiunile din bara laterală pentru a naviga între aplicații:  "
    "- **Selector Măști**: extrage obiecte și generează măști pentru imagini.  "
    "- **Clasificator Forme**: clasifică obiecte extrase în forme geometrice (triunghi, pătrat, dreptunghi, arc)."
)

st.markdown("---")
st.write(
    "În bara laterală vei găsi cele două aplicații disponibile.  "
    "Selectează-le pentru a deschide interfața fiecăreia."
)
