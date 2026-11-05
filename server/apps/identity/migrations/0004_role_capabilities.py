from django.db import migrations


def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    content_type, _ = ContentType.objects.using(database).get_or_create(app_label="identity", model="user")
    permissions = {}
    for code, name in {
        "view_user": "Can view user",
        "add_user": "Can add user",
        "change_user": "Can change user",
        "revoke_loginsession": "Can revoke customer login sessions",
    }.items():
        permissions[code], _ = Permission.objects.using(database).get_or_create(
            content_type=content_type, codename=code, defaults={"name": name}
        )
    for role in ("SUPERADMIN", "PRODUCT_MANAGER", "OPERATOR", "AUDITOR", "CUSTOMER"):
        group, created = Group.objects.using(database).get_or_create(name=f"identity-role:{role}")
        if created and role == "AUDITOR":
            group.permissions.add(permissions["view_user"])


class Migration(migrations.Migration):
    dependencies = [("identity", "0003_alter_user_options")]
    operations = [migrations.RunPython(seed_roles, migrations.RunPython.noop)]
