def _setup_two_player_tournament(client):
    p1 = client.post("/players", json={"name": "Alice", "rating": 1400}).json()
    p2 = client.post("/players", json={"name": "Bob", "rating": 1200}).json()
    tournament = client.post(
        "/tournaments",
        json={
            "name": "T",
            "date": "2026-04-01",
            "location": "A",
            "surface": "Hard",
            "player_ids": [p1["id"], p2["id"]],
        },
    ).json()
    bracket = client.post(f"/tournaments/{tournament['id']}/bracket").json()
    match = bracket["rounds"][0][0]
    return p1, p2, tournament, match


def test_record_match_result(client):
    p1, p2, tournament, match = _setup_two_player_tournament(client)
    resp = client.post(
        f"/matches/{match['id']}/result",
        json={"winner_id": p1["id"], "score": "6-4, 6-3"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["winner_id"] == p1["id"]
    assert body["score"] == "6-4, 6-3"


def test_record_match_result_completes_tournament(client):
    p1, p2, tournament, match = _setup_two_player_tournament(client)
    client.post(f"/matches/{match['id']}/result", json={"winner_id": p1["id"], "score": "6-4, 6-3"})
    resp = client.get(f"/tournaments/{tournament['id']}")
    assert resp.json()["status"] == "complete"


def test_record_match_result_updates_ratings(client):
    p1, p2, tournament, match = _setup_two_player_tournament(client)
    client.post(f"/matches/{match['id']}/result", json={"winner_id": p1["id"], "score": "6-4, 6-3"})
    winner = client.get(f"/players/{p1['id']}").json()
    loser = client.get(f"/players/{p2['id']}").json()
    assert winner["rating"] > 1400
    assert loser["rating"] < 1200


def test_record_match_result_not_found(client):
    resp = client.post("/matches/999/result", json={"winner_id": 1, "score": "6-0, 6-0"})
    assert resp.status_code == 404


def test_record_match_result_invalid_winner(client):
    p1, p2, tournament, match = _setup_two_player_tournament(client)
    other = client.post("/players", json={"name": "Carl"}).json()
    resp = client.post(
        f"/matches/{match['id']}/result",
        json={"winner_id": other["id"], "score": "6-0, 6-0"},
    )
    assert resp.status_code == 422


def test_record_match_result_already_decided(client):
    p1, p2, tournament, match = _setup_two_player_tournament(client)
    client.post(f"/matches/{match['id']}/result", json={"winner_id": p1["id"], "score": "6-4, 6-3"})
    resp = client.post(f"/matches/{match['id']}/result", json={"winner_id": p2["id"], "score": "6-4, 6-3"})
    assert resp.status_code == 422


def test_advances_winner_to_next_round(client):
    players = [
        client.post("/players", json={"name": f"P{i}", "rating": 1200 + i}).json() for i in range(4)
    ]
    tournament = client.post(
        "/tournaments",
        json={
            "name": "T",
            "date": "2026-04-01",
            "location": "A",
            "surface": "Hard",
            "player_ids": [p["id"] for p in players],
        },
    ).json()
    bracket = client.post(f"/tournaments/{tournament['id']}/bracket").json()
    round1 = bracket["rounds"][0]

    for match in round1:
        winner_id = match["player_a_id"]
        client.post(f"/matches/{match['id']}/result", json={"winner_id": winner_id, "score": "6-0, 6-0"})

    updated = client.get(f"/tournaments/{tournament['id']}/bracket").json()
    round2 = updated["rounds"][1]
    assert round2[0]["player_a_id"] is not None
    assert round2[0]["player_b_id"] is not None
