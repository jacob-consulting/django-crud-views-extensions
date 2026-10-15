from django.contrib.auth import get_user_model

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # local example only — shown on the home and login pages


def ensure_admin():
    """Create the admin superuser, or reset its password. Idempotent."""
    user, _ = get_user_model().objects.get_or_create(
        username=ADMIN_USERNAME, defaults={"is_superuser": True, "is_staff": True}
    )
    user.is_superuser = user.is_staff = True
    user.set_password(ADMIN_PASSWORD)
    user.save()
    return user
