import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_project(client):
    r = client.post("/api/v1/requirements/projects", json={"name": "Sistema Bancário", "domain": "financeiro"})
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert body["name"] == "Sistema Bancário"


def test_elicit_requirements(client):
    proj = client.post("/api/v1/requirements/projects", json={"name": "Proj Elicit"}).json()
    r = client.post(
        f"/api/v1/requirements/projects/{proj['id']}/elicit",
        json={"raw_input": "O sistema deve permitir login com e-mail e senha do usuário cadastrado"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "session_id" in body
    assert isinstance(body["requirements"], list)
    assert "gaps_detected" in body


def test_elicit_nonexistent_project_returns_404(client):
    r = client.post(
        "/api/v1/requirements/projects/nonexistent-id/elicit",
        json={"raw_input": "teste de sistema"},
    )
    assert r.status_code == 404


def test_list_requirements_empty_project(client):
    proj = client.post("/api/v1/requirements/projects", json={"name": "Vazio"}).json()
    r = client.get(f"/api/v1/requirements/projects/{proj['id']}")
    assert r.status_code == 200
    assert r.json() == []


def test_refine_nonexistent_returns_422(client):
    r = client.patch(
        "/api/v1/requirements/nonexistent-id/refine",
        json={"title": "Novo título"},
    )
    assert r.status_code == 422


def test_approve_nonexistent_returns_422(client):
    r = client.post(
        "/api/v1/requirements/nonexistent-id/approve",
        json={"approved_by": "user-1"},
    )
    assert r.status_code == 422


def test_full_api_workflow(client):
    # Criar projeto
    proj = client.post("/api/v1/requirements/projects", json={
        "name": "E-commerce", "domain": "varejo"
    }).json()
    project_id = proj["id"]

    # Elicitar
    elicit_r = client.post(
        f"/api/v1/requirements/projects/{project_id}/elicit",
        json={"raw_input": "O cliente deve poder adicionar produtos ao carrinho e finalizar compra com cartão de crédito"},
    )
    assert elicit_r.status_code == 200
    reqs = elicit_r.json()["requirements"]

    if reqs:
        req_id = reqs[0]["id"]
        # Refinar
        refine_r = client.patch(
            f"/api/v1/requirements/{req_id}/refine",
            json={"description": "Adicionar ao carrinho com validação de estoque", "changelog": "v2"},
        )
        assert refine_r.status_code == 200

    # Listar
    list_r = client.get(f"/api/v1/requirements/projects/{project_id}")
    assert list_r.status_code == 200
