def test_create_player_returns_201_and_player(client):
    resp = client.post("/players", json={"name": "Alice", "rating": 1300})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Alice"
    assert body["rating"] == 1300
    assert "id" in body
    assert "created" in body


def test_create_player_defaults_rating(client):
    resp = client.post("/players", json={"name": "Bob"})
    assert resp.status_code == 201
    assert resp.json()["rating"] == 1200.0


def test_list_players_empty(client):
    resp = client.get("/players")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_players_sorted_by_name(client):
    client.post("/players", json={"name": "Zed"})
    client.post("/players", json={"name": "Amy"})
    resp = client.get("/players")
    names = [p["name"] for p in resp.json()]
    assert names == ["Amy", "Zed"]


def test_get_player_found(client):
    created = client.post("/players", json={"name": "Alice"}).json()
    resp = client.get(f"/players/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"


def test_get_player_not_found(client):
    resp = client.get("/players/999")
    assert resp.status_code == 404


def test_player_stats_no_matches(client):
    created = client.post("/players", json={"name": "Alice"}).json()
    resp = client.get(f"/players/{created['id']}/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["wins"] == 0
    assert body["losses"] == 0
    assert body["win_ratio"] == 0.0
    assert body["streak_type"] is None
    assert len(body["rating_history"]) == 1


def test_player_stats_not_found(client):
    resp = client.get("/players/999/stats")
    assert resp.status_code == 404


def test_player_stats_after_match(client):
    p1 = client.post("/players", json={"name": "Alice", "rating": 1400}).json()
    p2 = client.post("/players", json={"name": "Bob", "rating": 1200}).json()
    tournament = client.post(
        "/tournaments",
        json={
            "name": "Test Open",
            "date": "2026-01-01",
            "location": "Court 1",
            "surface": "Hard",
            "player_ids": [p1["id"], p2["id"]],
        },
    ).json()
    bracket = client.post(f"/tournaments/{tournament['id']}/bracket").json()
    match = bracket["rounds"][0][0]

    resp = client.post(
        f"/matches/{match['id']}/result",
        json={"winner_id": p1["id"], "score": "6-4, 6-3"},
    )
    assert resp.status_code == 200

    stats = client.get(f"/players/{p1['id']}/stats").json()
    assert stats["wins"] == 1
    assert stats["losses"] == 0
    assert stats["win_ratio"] == 1.0
    assert stats["streak"] == 1
    assert stats["streak_type"] == "W"
    assert len(stats["rating_history"]) == 2
