import uuid

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """Custom queryset for soft-deletable models."""

    def delete(self, hard: bool = False):
        if hard:
            return super().delete()
        # Trigger instance-level soft deletes to ensure cascade logic executes
        count = 0
        for obj in self:
            obj.delete(hard=False)
            count += 1
        return count, {self.model._meta.label: count}

    def hard_delete(self):
        return super().delete()

    def restore(self, cascade: bool = True):
        count = 0
        for obj in self:
            obj.restore(cascade=cascade)
            count += 1
        return count

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """
    Default manager for BaseModel.
    Automatically filters out soft-deleted records on all standard queries.
    Provides all_with_deleted() and deleted_only() for administrative/audit access.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)

    def hard_delete(self):
        return self.get_queryset().hard_delete()

    def restore(self, cascade: bool = True):
        return self.all_with_deleted().filter(is_deleted=True).restore(cascade=cascade)


class SoftDeleteAllManager(models.Manager):
    """Unfiltered manager providing access to all records regardless of is_deleted flag."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """
    Abstract base entity for all domain models.
    Provides UUID primary key, timestamps, and soft-delete capabilities.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Cryptographically strong UUIDv4 identifier",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when entity was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when entity was last updated",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when entity was soft-deleted (null if active)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Operational toggle (active/inactive)",
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft-delete flag",
    )

    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def delete(self, using=None, keep_parents=False, hard: bool = False):
        """
        Soft deletes the record by default. Sets hard=True for permanent DB deletion.
        Cascades soft-delete to related objects with on_delete=CASCADE.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        # Soft-delete cascade on related reverse foreign keys
        for rel in self._meta.related_objects:
            if rel.on_delete == models.CASCADE:
                accessor_name = rel.get_accessor_name()
                if not accessor_name or not hasattr(self, accessor_name):
                    continue

                related = getattr(self, accessor_name)
                if hasattr(related, "all_with_deleted"):
                    for item in related.all_with_deleted():
                        if hasattr(item, "delete"):
                            item.delete(hard=False)
                elif hasattr(related, "all"):
                    for item in related.all():
                        if hasattr(item, "delete"):
                            item.delete(hard=False)
                elif hasattr(related, "delete"):
                    # OneToOneRel
                    related.delete(hard=False)

        return 1, {self._meta.label: 1}

    def hard_delete(self, using=None, keep_parents=False):
        """Perform physical deletion from database."""
        return self.delete(using=using, keep_parents=keep_parents, hard=True)

    def restore(self, cascade: bool = True):
        """
        Restores a soft-deleted record and optionally cascades restore to related objects.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        if cascade:
            for rel in self._meta.related_objects:
                if rel.on_delete == models.CASCADE:
                    accessor_name = rel.get_accessor_name()
                    if not accessor_name or not hasattr(self, accessor_name):
                        continue

                    related = getattr(self, accessor_name)
                    if hasattr(related, "all_with_deleted"):
                        for item in related.all_with_deleted():
                            if hasattr(item, "restore"):
                                item.restore(cascade=cascade)
                    elif hasattr(related, "restore"):
                        related.restore(cascade=cascade)
