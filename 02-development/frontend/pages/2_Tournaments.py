import streamlit as st

import backend_client as backend

st.set_page_config(page_title="Tournaments", page_icon="🏆", layout="wide")
st.title("🏆 Tournaments")

try:
    players = backend.list_players()
    existing_tournaments = backend.list_tournaments()
except backend.BackendError as exc:
    st.error(f"Could not load data from the backend: {exc}")
    st.stop()

with st.expander("➕ Create a new tournament", expanded=not existing_tournaments):
    if not players:
        st.warning("Add players first on the **Players** page.")
    else:
        with st.form("create_tournament_form"):
            name = st.text_input("Tournament name")
            tournament_date = st.date_input("Date")
            location = st.text_input("Location")
            surface = st.selectbox("Surface", backend.SURFACES)
            selected_names = st.multiselect(
                "Players (select at least 2)",
                [p["name"] for p in players],
            )
            submitted = st.form_submit_button("Create tournament")

            if submitted:
                if not name.strip():
                    st.error("Please enter a tournament name.")
                elif len(selected_names) < 2:
                    st.error("Select at least 2 players.")
                else:
                    player_ids = [p["id"] for p in players if p["name"] in selected_names]
                    try:
                        tournament = backend.create_tournament(
                            name.strip(), tournament_date, location.strip(), surface, player_ids
                        )
                    except backend.BackendError as exc:
                        st.error(f"Could not create tournament: {exc}")
                    else:
                        st.session_state["selected_tournament_id"] = tournament["id"]
                        st.success(f"Created '{tournament['name']}'. Generate the bracket below.")
                        st.rerun()

st.subheader("All tournaments")
tournaments = existing_tournaments

if not tournaments:
    st.info("No tournaments yet.")
else:
    for tournament in tournaments:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{tournament['name']}** — {tournament['date']} — {tournament['location']} ({tournament['surface']})")
                st.caption(f"{len(tournament['player_ids'])} players — status: {tournament['status']}")
            with col2:
                if tournament["status"] == "setup":
                    if st.button("Generate bracket", key=f"gen_{tournament['id']}"):
                        try:
                            backend.generate_bracket(tournament["id"])
                        except backend.BackendError as exc:
                            st.error(f"Could not generate bracket: {exc}")
                        else:
                            st.session_state["selected_tournament_id"] = tournament["id"]
                            st.success("Bracket generated — open the Bracket page.")
                            st.rerun()
                else:
                    if st.button("View bracket", key=f"view_{tournament['id']}"):
                        st.session_state["selected_tournament_id"] = tournament["id"]
                        st.switch_page("pages/3_Bracket.py")
