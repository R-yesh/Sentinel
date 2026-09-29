import importlib
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from apps.api.app import main

from apps.api.app.core.config import Settings
from deployment.preflight import check_runtime


def test_exact_cors_configuration(monkeypatch):
    monkeypatch.setenv('SENTINEL_CORS_ORIGINS', '["https://sentinel-demo.vercel.app","http://localhost:5173"]')
    origins = Settings().sentinel_cors_origins
    monkeypatch.setattr(main.settings, 'sentinel_cors_origins', origins)
    monkeypatch.setattr(main, 'app', main.app)  # Restore original app after reload/test.
    importlib.reload(main)
    with TestClient(main.app) as client:
        headers = {'Origin': origins[0], 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'}
        allowed = client.options('/api/v1/investigations', headers=headers)
        assert allowed.status_code == 200
        assert allowed.headers['access-control-allow-origin'] == origins[0]
        assert 'access-control-allow-credentials' not in allowed.headers
        headers['Origin'] = 'https://untrusted.example'
        denied = client.options('/api/v1/investigations', headers=headers)
        assert denied.status_code == 400
        assert 'access-control-allow-origin' not in denied.headers


@pytest.mark.parametrize('origin', ['*', 'https://*.vercel.app', 'https://example.com/path', 'https://user:secret@example.com'])
def test_cors_rejects_broad_or_non_origin_values(origin):
    with pytest.raises(ValidationError):
        Settings(sentinel_cors_origins=[origin])


def test_packaged_runtime_assets():
    check_runtime()
