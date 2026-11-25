from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core import mail
from rest_framework.test import APIClient

from inventory.models import StockMovement
from inventory.tasks import generate_daily_stock_report

pytestmark = pytest.mark.django_db


def test_dashboard_stats(staff_client, stocked):
    warehouse, p1, p2 = stocked
    StockMovement.objects.create(
        product=p2, warehouse=warehouse, movement_type="OUT", quantity=3
    )  # p2: 2 left, threshold 3 -> low
    response = staff_client.get("/api/dashboard/stats/")
    assert response.status_code == 200
    data = response.data
    assert data["total_products"] == 2
    assert data["low_stock_count"] == 1
    assert Decimal(data["inventory_value"]) == Decimal("64.00")  # 10*4 + 2*12
    assert data["top_products"] == [
        {"name": p1.name, "quantity": 10},
        {"name": p2.name, "quantity": 2},
    ]


def test_dashboard_top_products_sum_all_warehouses(staff_client, stocked):
    from .factories import WarehouseFactory

    _, p1, p2 = stocked
    StockMovement.objects.create(
        product=p2, warehouse=WarehouseFactory(), movement_type="IN", quantity=20
    )
    top = staff_client.get("/api/dashboard/stats/").data["top_products"]
    assert top[0] == {"name": p2.name, "quantity": 25}
    assert len(top) == 2


def test_dashboard_requires_login(anon_client):
    assert anon_client.get("/api/dashboard/stats/").status_code == 401


def test_health_is_public(anon_client):
    response = anon_client.get("/api/health/")
    assert response.status_code == 200
    assert response.data == {"status": "ok"}


def test_jwt_login_and_use(db):
    User.objects.create_user(username="alice", password="s3cret-pass")
    client = APIClient()
    response = client.post(
        "/api/auth/login/", {"username": "alice", "password": "s3cret-pass"}, format="json"
    )
    assert response.status_code == 200
    token = response.data["access"]
    assert (
        client.post(
            "/api/auth/refresh/", {"refresh": response.data["refresh"]}, format="json"
        ).status_code
        == 200
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/products/").status_code == 200


def test_jwt_login_rejects_bad_password(db):
    User.objects.create_user(username="alice", password="s3cret-pass")
    response = APIClient().post(
        "/api/auth/login/", {"username": "alice", "password": "wrong"}, format="json"
    )
    assert response.status_code == 401


def test_low_stock_alert_is_mailed_after_commit(stocked, django_capture_on_commit_callbacks):
    warehouse, p1, _ = stocked
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        StockMovement.objects.create(
            product=p1, warehouse=warehouse, movement_type="OUT", quantity=8
        )
    assert len(mail.outbox) == 1
    assert p1.name in mail.outbox[0].subject


def test_daily_report_lists_low_items(stocked):
    warehouse, p1, p2 = stocked
    StockMovement.objects.create(product=p2, warehouse=warehouse, movement_type="OUT", quantity=4)
    mail.outbox.clear()
    assert generate_daily_stock_report() == "Report sent: 1 low item(s)"
    assert p2.name in mail.outbox[0].body
    assert p1.name not in mail.outbox[0].body


def test_api_docs_render(staff_client):
    assert staff_client.get("/api/schema/").status_code == 200
    response = staff_client.get("/api/docs/")
    assert response.status_code == 200
    assert b"cdn.jsdelivr" not in response.content  # assets are served locally
