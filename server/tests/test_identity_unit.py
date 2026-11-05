import importlib
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from apps.identity.models import phone_validator


@pytest.mark.parametrize("phone", ["+989121234567", "+14155552671"])
def test_international_phone_validation(phone):
    phone_validator(phone)


@pytest.mark.parametrize("phone", ["09121234567", "+0123456789", "+98<script>"])
def test_rejects_invalid_international_phone(phone):
    with pytest.raises(ValidationError):
        phone_validator(phone)


def test_migration_refuses_to_orphan_legacy_accounts():
    migration = importlib.import_module("apps.identity.migrations.0001_initial")
    editor = MagicMock()
    editor.connection.introspection.table_names.return_value = ["auth_user"]
    cursor = editor.connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)
    with pytest.raises(RuntimeError, match="Legacy auth users exist"):
        migration.require_empty_legacy_users(None, editor)
    cursor.fetchone.return_value = (0,)
    migration.require_empty_legacy_users(None, editor)
    editor.connection.introspection.table_names.return_value = []
    migration.require_empty_legacy_users(None, editor)
