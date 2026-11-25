import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import Client

BACKEND = Path(__file__).resolve().parents[2]

PROBE = (
    "import json, django; django.setup(); from django.conf import settings as s; "
    "print(json.dumps({'debug': s.DEBUG, 'hosts': s.ALLOWED_HOSTS, "
    "'csrf': s.CSRF_TRUSTED_ORIGINS, 'proxy': list(s.SECURE_PROXY_SSL_HEADER or []), "
    "'session_secure': s.SESSION_COOKIE_SECURE, 'csrf_secure': s.CSRF_COOKIE_SECURE, "
    "'cors': s.CORS_ALLOWED_ORIGINS, 'db': s.DATABASES['default']['ENGINE'], "
    "'db_host': s.DATABASES['default'].get('HOST'), "
    "'email': s.EMAIL_BACKEND, 'num_proxies': s.REST_FRAMEWORK.get('NUM_PROXIES')}))"
)


def _run(env_overrides):
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DJANGO_", "SECRET_KEY", "DEBUG", "DATABASE_URL", "POSTGRES_"))
    }
    env.update({"DJANGO_SETTINGS_MODULE": "config.settings", **env_overrides})
    return subprocess.run(  # noqa: S603
        [sys.executable, "-c", PROBE], cwd=BACKEND, env=env, capture_output=True, text=True
    )


PROD = {
    "DJANGO_PRODUCTION": "True",
    "SECRET_KEY": "k" * 30 + "-production-test-key-0123456789",
    "ALLOWED_HOSTS": "stockflow.demo.karbaschian.com,localhost",
    "CSRF_TRUSTED_ORIGINS": "https://stockflow.demo.karbaschian.com",
    "POSTGRES_HOST": "db",
    "POSTGRES_PASSWORD": "x",
    "DRF_NUM_PROXIES": "1",
}


def test_production_settings():
    result = _run(PROD)
    assert result.returncode == 0, result.stderr
    cfg = json.loads(result.stdout.strip().splitlines()[-1])
    assert cfg["debug"] is False
    assert cfg["hosts"] == ["stockflow.demo.karbaschian.com", "localhost"]
    assert cfg["csrf"] == ["https://stockflow.demo.karbaschian.com"]
    assert cfg["proxy"] == ["HTTP_X_FORWARDED_PROTO", "https"]
    assert cfg["session_secure"] and cfg["csrf_secure"]
    assert cfg["cors"] == []
    assert cfg["db"] == "django.db.backends.postgresql"
    assert cfg["db_host"] == "db"
    assert cfg["email"] == "django.core.mail.backends.console.EmailBackend"
    assert cfg["num_proxies"] == 1


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"SECRET_KEY": ""}, "SECRET_KEY must be set"),
        ({"SECRET_KEY": "short"}, "at least 50"),
        ({"DEBUG": "True"}, "DEBUG must be off"),
    ],
)
def test_production_refuses_unsafe_config(overrides, message):
    result = _run({**PROD, **overrides})
    assert result.returncode != 0
    assert message in result.stderr


def test_development_defaults():
    result = _run({})
    assert result.returncode == 0, result.stderr
    cfg = json.loads(result.stdout.strip().splitlines()[-1])
    assert cfg["proxy"] == []
    assert cfg["db"] == "django.db.backends.sqlite3"
    assert "http://localhost:5173" in cfg["cors"]


@pytest.fixture
def frontend_build(tmp_path, settings):
    (tmp_path / "index.html").write_text("<!doctype html><div id=root></div>")
    settings.FRONTEND_DIST = tmp_path
    return tmp_path


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/", "/login", "/stock", "/orders/new", "/administration"])
def test_spa_routes_serve_index(frontend_build, path):
    response = Client().get(path)
    assert response.status_code == 200
    assert b"id=root" in b"".join(response.streaming_content)
    assert "no-cache" in response["Cache-Control"]


@pytest.mark.django_db
def test_api_and_admin_are_not_swallowed_by_the_spa(frontend_build):
    client = Client()
    assert client.get("/api/does-not-exist/").status_code == 404
    assert client.get("/admin").status_code == 301  # APPEND_SLASH still applies
    assert client.get("/admin/").status_code == 302  # login redirect


@pytest.mark.django_db
def test_spa_without_build_is_404(settings, tmp_path):
    settings.FRONTEND_DIST = tmp_path / "missing"
    assert Client().get("/stock").status_code == 404
