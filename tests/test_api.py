from tests.conftest import register_and_login

RECIPE = {"title": "Ratatouille", "duration": 75, "servings": 4}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_me(client):
    headers = register_and_login(client, "alice")
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert "hashed_password" not in response.json()


def test_register_duplicate_username(client):
    register_and_login(client, "alice")
    response = client.post("/auth/register", json={
        "username": "alice", "email": "other@example.com", "password": "password123",
    })
    assert response.status_code == 409


def test_login_wrong_password(client):
    register_and_login(client, "alice")
    response = client.post("/auth/login", json={"username": "alice", "password": "mauvais-mdp"})
    assert response.status_code == 401


def test_recipes_require_token(client):
    assert client.get("/recipes").status_code in (401, 403)


def test_recipe_crud(client):
    headers = register_and_login(client, "alice")

    created = client.post("/recipes", json=RECIPE, headers=headers)
    assert created.status_code == 201
    recipe_id = created.json()["id"]

    updated = client.put(f"/recipes/{recipe_id}", json={**RECIPE, "servings": 6}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["servings"] == 6

    assert client.delete(f"/recipes/{recipe_id}", headers=headers).status_code == 204
    assert client.get(f"/recipes/{recipe_id}", headers=headers).status_code == 404


def test_search_filters(client):
    headers = register_and_login(client, "alice")
    client.post("/recipes", json=RECIPE, headers=headers)
    client.post("/recipes", json={"title": "Crêpes", "duration": 30, "servings": 2}, headers=headers)

    titles = lambda r: [x["title"] for x in r.json()]
    assert titles(client.get("/recipes?query=rata", headers=headers)) == ["Ratatouille"]
    assert titles(client.get("/recipes?duration=40", headers=headers)) == ["Crêpes"]
    assert titles(client.get("/recipes?servings=3", headers=headers)) == ["Ratatouille"]


def test_sharing_read_only_then_edit(client):
    alice = register_and_login(client, "alice")
    bob = register_and_login(client, "bobby")
    recipe_id = client.post("/recipes", json=RECIPE, headers=alice).json()["id"]

    # Sans partage, Bob ne voit rien
    assert client.get(f"/recipes/{recipe_id}", headers=bob).status_code == 403

    # Partage en lecture seule : lecture OK, modification refusée
    client.post("/users/me/accesses", json={"username": "bobby"}, headers=alice)
    assert client.get(f"/recipes/{recipe_id}", headers=bob).status_code == 200
    assert client.put(f"/recipes/{recipe_id}", json=RECIPE, headers=bob).status_code == 403

    # Partage en modification : modification OK, suppression toujours réservée au propriétaire
    client.post("/users/me/accesses", json={"username": "bobby", "can_edit": True}, headers=alice)
    assert client.put(f"/recipes/{recipe_id}", json=RECIPE, headers=bob).status_code == 200
    assert client.delete(f"/recipes/{recipe_id}", headers=bob).status_code == 403
