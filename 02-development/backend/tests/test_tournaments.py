def _make_players(client, count_=4, ratings=None):
    players = []
    for i in range(count_):
        rating = ratings[i] if ratings else 1200
        players.append(client.post("/players", json={"name": f"Player{i}", "rating": rating}).json())
    return players


def test_create_tournament(client):
    players = _make_players(client, 4)
    resp = client.post(
        "/tournaments",
        json={
            "name": "Spring Open",
            "date": "2026-04-01",
            "location": "Club A",
            "surface": "Clay",
            "player_ids": [p["id"] for p in players],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Spring Open"
    assert body["status"] == "setup"
    assert len(body["player_ids"]) == 4


def test_create_tournament_requires_two_players(client):
    players = _make_players(client, 1)
    resp = client.post(
        "/tournaments",
        json={
            "name": "Solo",
            "date": "2026-04-01",
            "location": "Club A",
            "surface": "Clay",
            "player_ids": [players[0]["id"]],
        },
    )
    assert resp.status_code == 422


def test_create_tournament_unknown_player(client):
    resp = client.post(
        "/tournaments",
        json={
            "name": "Ghosts",
            "date": "2026-04-01",
            "location": "Club A",
            "surface": "Clay",
            "player_ids": [1, 2],
        },
    )
    assert resp.status_code == 422


def test_list_tournaments(client):
    players = _make_players(client, 2)
    client.post(
        "/tournaments",
        json={
            "name": "T1",
            "date": "2026-04-01",
            "location": "A",
            "surface": "Hard",
            "player_ids": [p["id"] for p in players],
        },
    )
    resp = client.get("/tournaments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_tournament_not_found(client):
    resp = client.get("/tournaments/999")
    assert resp.status_code == 404


def test_generate_bracket_pairs_top_seed_with_bye_for_odd_count(client):
    players = _make_players(client, 3, ratings=[1500, 1400, 1300])
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

    resp = client.post(f"/tournaments/{tournament['id']}/bracket")
    assert resp.status_code == 201
    bracket = resp.json()
    assert len(bracket["rounds"]) == 2  # 3 players -> bracket size 4 -> 2 rounds
    round1 = bracket["rounds"][0]
    assert len(round1) == 2

    top_seed_match = next(
        m for m in round1 if players[0]["id"] in (m["player_a_id"], m["player_b_id"])
    )
    assert top_seed_match["is_bye"] is True
    assert top_seed_match["winner_id"] == players[0]["id"]


def test_generate_bracket_already_generated(client):
    players = _make_players(client, 2)
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
    client.post(f"/tournaments/{tournament['id']}/bracket")
    resp = client.post(f"/tournaments/{tournament['id']}/bracket")
    assert resp.status_code == 409


def test_get_bracket_before_generation(client):
    players = _make_players(client, 2)
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
    resp = client.get(f"/tournaments/{tournament['id']}/bracket")
    assert resp.status_code == 409


def test_get_bracket_after_generation(client):
    players = _make_players(client, 2)
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
    client.post(f"/tournaments/{tournament['id']}/bracket")
    resp = client.get(f"/tournaments/{tournament['id']}/bracket")
    assert resp.status_code == 200
    assert len(resp.json()["rounds"][0]) == 1
