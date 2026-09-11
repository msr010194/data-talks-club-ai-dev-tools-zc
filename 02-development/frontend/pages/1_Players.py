import streamlit as st

import backend_client as backend

st.set_page_config(page_title="Players", page_icon="👤", layout="wide")
st.title("👤 Players")

with st.expander("➕ Add a new player", expanded=False):
    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Name")
        rating = st.number_input("Starting rating", min_value=0.0, value=1200.0, step=10.0)
        submitted = st.form_submit_button("Add player")
        if submitted:
            if not name.strip():
                st.error("Please enter a player name.")
            else:
                try:
                    backend.create_player(name.strip(), rating)
                except backend.BackendError as exc:
                    st.error(f"Could not add player: {exc}")
                else:
                    st.success(f"Added {name.strip()}.")
                    st.rerun()

try:
    players = backend.list_players()
except backend.BackendError as exc:
    st.error(f"Could not load data from the backend: {exc}")
    st.stop()

st.subheader("Player database")
if not players:
    st.info("No players yet — add one above.")
else:
    st.dataframe(
        [{"Name": p["name"], "Rating": p["rating"], "Created": p["created"]} for p in players],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("Player profile")

if players:
    selected_name = st.selectbox("Select a player", [p["name"] for p in players])
    selected = next(p for p in players if p["name"] == selected_name)
    try:
        stats = backend.get_player_stats(selected["id"])
    except backend.BackendError as exc:
        st.error(f"Could not load player stats: {exc}")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rating", selected["rating"])
    col2.metric("Win ratio", f"{stats['win_ratio']:.0%}")
    col3.metric("Record", f"{stats['wins']}-{stats['losses']}")
    streak_label = "—" if stats["streak_type"] is None else f"{stats['streak']}{stats['streak_type']}"
    col4.metric("Current streak", streak_label)

    st.markdown("**Rating trend**")
    history = stats["rating_history"]
    st.line_chart(
        {"rating": [h["rating"] for h in history]},
    )
else:
    st.info("Add players to see profiles here.")
