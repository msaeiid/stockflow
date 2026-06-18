import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_anonymous_cannot_list_products():
    client = APIClient()
    response = client.get("/api/products/")
    assert response.status_code == 401


def test_employee_cannot_create_category():
    employee = User.objects.create_user(username="emp", password="pass12345")
    employee.groups.add(Group.objects.create(name="Employee"))
    client = APIClient()
    client.force_authenticate(user=employee)
    response = client.post("/api/categories/", {"name": "Tools"})
    assert response.status_code == 403


def test_manager_can_create_category():
    manager = User.objects.create_user(username="mgr", password="pass12345")
    manager.groups.add(Group.objects.create(name="Manager"))
    client = APIClient()
    client.force_authenticate(user=manager)
    response = client.post("/api/categories/", {"name": "Tools"})
    assert response.status_code == 201
