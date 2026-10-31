import pytest
from django.apps import apps
from django.urls import Resolver404, resolve


def test_django_admin_is_not_installed():
    assert not apps.is_installed("django.contrib.admin")


@pytest.mark.parametrize("path", ["/admin/", "/admin/login/", "/admin/auth/user/"])
def test_django_admin_routes_are_not_exposed(path):
    with pytest.raises(Resolver404):
        resolve(path)


def test_health_route_remains_available():
    assert resolve("/api/health/").url_name == "health-check"
