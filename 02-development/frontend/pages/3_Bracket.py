import streamlit as st

import backend_client as backend

st.set_page_config(page_title="Bracket", page_icon="📊", layout="wide")
st.title("📊 Bracket")

try:
    tournaments = [t for t in backend.list_tournaments() if t["status"] != "setup"]
except backend.BackendError as exc:
    st.error(f"Could not load data from the backend: {exc}")
    st.stop()

if not tournaments:
    st.info("No brackets yet — generate one from the **Tournaments** page.")
    st.stop()

names = [f"{t['name']} ({t['date']})" for t in tournaments]
default_id = st.session_state.get("selected_tournament_id")
default_index = next(
    (i for i, t in enumerate(tournaments) if t["id"] == default_id), 0
)
selected_index = st.selectbox("Tournament", range(len(names)), format_func=lambda i: names[i], index=default_index)
tournament = tournaments[selected_index]
st.session_state["selected_tournament_id"] = tournament["id"]

if tournament["status"] == "complete":
    st.success("🏆 Tournament complete!")

try:
    bracket = backend.get_bracket(tournament["id"])
except backend.BackendError as exc:
    st.error(f"Could not load bracket: {exc}")
    st.stop()


def player_label(player_id):
    if player_id is None:
        return "TBD"
    return backend.get_player(player_id)["name"]


columns = st.columns(len(bracket))

for round_idx, (col, round_matches) in enumerate(zip(columns, bracket)):
    with col:
        st.markdown(f"**Round {round_idx + 1}**")
        for match in round_matches:
            with st.container(border=True):
                a_name = player_label(match["player_a_id"])
                b_name = player_label(match["player_b_id"])

                if match["is_bye"]:
                    st.markdown(f"{a_name if match['player_a_id'] else b_name} — **bye**")
                    continue

                if match["winner_id"]:
                    winner_name = player_label(match["winner_id"])
                    st.markdown(f"~~{a_name}~~" if match["winner_id"] != match["player_a_id"] else f"**{a_name}**")
                    st.markdown(f"~~{b_name}~~" if match["winner_id"] != match["player_b_id"] else f"**{b_name}**")
                    st.caption(f"Winner: {winner_name} — {match['score']}")
                elif match["player_a_id"] and match["player_b_id"]:
                    st.markdown(f"{a_name} vs {b_name}")
                    with st.form(f"match_{match['id']}"):
                        winner_choice = st.radio("Winner", [a_name, b_name], key=f"winner_{match['id']}")
                        score = st.text_input("Set scores (e.g. 6-4, 3-6, 6-2)", key=f"score_{match['id']}")
                        if st.form_submit_button("Record result"):
                            if not score.strip():
                                st.error("Enter the set scores.")
                            else:
                                winner_id = match["player_a_id"] if winner_choice == a_name else match["player_b_id"]
                                try:
                                    backend.record_match_result(match["id"], winner_id, score.strip())
                                except backend.BackendError as exc:
                                    st.error(f"Could not record result: {exc}")
                                else:
                                    st.rerun()
                else:
                    st.markdown(f"{a_name}")
                    st.markdown(f"{b_name}")
                    st.caption("Waiting for opponent")
