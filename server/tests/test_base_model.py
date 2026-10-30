import pytest
from django.db import connection, models
from django.db.models.deletion import CASCADE

from apps.core.models import BaseModel

pytestmark = pytest.mark.integration


class DummyParent(BaseModel):
    name = models.CharField(max_length=100)

    class Meta(BaseModel.Meta):
        app_label = "core"


class DummyChild(BaseModel):
    parent = models.ForeignKey(DummyParent, on_delete=CASCADE, related_name="children")
    title = models.CharField(max_length=100)

    class Meta(BaseModel.Meta):
        app_label = "core"


@pytest.fixture(scope="session", autouse=True)
def setup_test_tables(django_db_setup, django_db_blocker):
    """Create session-wide test tables for dummy models."""
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS core_dummychild CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS core_dummyparent CASCADE;")
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyParent)
            schema_editor.create_model(DummyChild)
        yield
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS core_dummychild CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS core_dummyparent CASCADE;")


@pytest.mark.django_db
def test_base_model_defaults_and_uuid():
    parent = DummyParent.objects.create(name="Parent 1")
    assert parent.id is not None
    assert parent.is_active is True
    assert parent.is_deleted is False
    assert parent.deleted_at is None
    assert parent.created_at is not None
    assert parent.updated_at is not None


@pytest.mark.django_db
def test_soft_delete_and_managers():
    parent = DummyParent.objects.create(name="Active Parent")
    parent_id = parent.id

    # Default queryset includes active
    assert DummyParent.objects.filter(id=parent_id).exists()
    assert DummyParent.objects.count() == 1

    # Perform soft delete
    parent.delete()

    # Model attributes updated
    parent.refresh_from_db()
    assert parent.is_deleted is True
    assert parent.deleted_at is not None

    # Default manager excludes soft-deleted
    assert not DummyParent.objects.filter(id=parent_id).exists()
    assert DummyParent.objects.count() == 0

    # all_with_deleted includes it
    assert DummyParent.objects.all_with_deleted().filter(id=parent_id).exists()
    assert DummyParent.all_objects.filter(id=parent_id).exists()

    # deleted_only includes it
    assert DummyParent.objects.deleted_only().filter(id=parent_id).exists()
    assert DummyParent.objects.deleted_only().count() == 1


@pytest.mark.django_db
def test_restore():
    parent = DummyParent.objects.create(name="Restorable Parent")
    parent.delete()
    assert DummyParent.objects.count() == 0

    parent.restore()
    parent.refresh_from_db()
    assert parent.is_deleted is False
    assert parent.deleted_at is None
    assert DummyParent.objects.count() == 1


@pytest.mark.django_db
def test_hard_delete():
    parent = DummyParent.objects.create(name="Physical Delete")
    parent_id = parent.id

    parent.hard_delete()
    assert not DummyParent.objects.all_with_deleted().filter(id=parent_id).exists()


@pytest.mark.django_db
def test_soft_delete_cascade_to_related_models():
    parent = DummyParent.objects.create(name="Parent with Children")
    child1 = DummyChild.objects.create(parent=parent, title="Child 1")
    child2 = DummyChild.objects.create(parent=parent, title="Child 2")

    assert DummyChild.objects.count() == 2

    # Soft delete parent -> should cascade soft delete to children
    parent.delete()

    child1.refresh_from_db()
    child2.refresh_from_db()

    assert parent.is_deleted is True
    assert child1.is_deleted is True
    assert child2.is_deleted is True
    assert child1.deleted_at is not None
    assert child2.deleted_at is not None

    # Excluded from default manager
    assert DummyChild.objects.count() == 0
    # Present in all_with_deleted
    assert DummyChild.objects.all_with_deleted().count() == 2

    # Restore parent with cascade -> should restore children
    parent.restore(cascade=True)
    child1.refresh_from_db()
    child2.refresh_from_db()

    assert parent.is_deleted is False
    assert child1.is_deleted is False
    assert child2.is_deleted is False
    assert DummyChild.objects.count() == 2


@pytest.mark.django_db
def test_queryset_soft_delete_and_restore():
    p1 = DummyParent.objects.create(name="Batch 1")
    p2 = DummyParent.objects.create(name="Batch 2")
    c1 = DummyChild.objects.create(parent=p1, title="Child B1")

    # Bulk soft delete via queryset
    DummyParent.objects.filter(id__in=[p1.id, p2.id]).delete()

    assert DummyParent.objects.count() == 0
    assert DummyParent.objects.all_with_deleted().count() == 2

    c1.refresh_from_db()
    assert c1.is_deleted is True

    # Bulk restore
    DummyParent.objects.restore(cascade=True)
    assert DummyParent.objects.count() == 2
    c1.refresh_from_db()
    assert c1.is_deleted is False
