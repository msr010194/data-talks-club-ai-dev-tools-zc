import streamlit as st

import backend_client as backend

st.set_page_config(page_title="Tennis Tournament Manager", page_icon="🎾", layout="wide")

st.title("🎾 Tennis Tournament Manager")
st.caption("Organizer dashboard — single-elimination tennis tournaments.")

players = backend.list_players()
tournaments = backend.list_tournaments()

col1, col2, col3 = st.columns(3)
col1.metric("Players", len(players))
col2.metric("Tournaments", len(tournaments))
col3.metric(
    "In progress",
    sum(1 for t in tournaments if t["status"] == "in_progress"),
)

st.subheader("Tournaments")
if not tournaments:
    st.info("No tournaments yet — create one from the **Tournaments** page.")
else:
    st.dataframe(
        [
            {
                "Name": t["name"],
                "Date": t["date"],
                "Location": t["location"],
                "Surface": t["surface"],
                "Players": len(t["player_ids"]),
                "Status": t["status"],
            }
            for t in tournaments
        ],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.markdown(
    "Use the sidebar to manage **Players**, set up **Tournaments**, and "
    "run the **Bracket** for an in-progress tournament."
)
