from importlib import import_module

from django.core.management.base import BaseCommand

from project.features import FEATURES
from project.seeding import ADMIN_PASSWORD, ADMIN_USERNAME, ensure_admin


class Command(BaseCommand):
    help = "Seed the admin user and demo data for all example apps. Idempotent."

    def handle(self, *args, **options):
        ensure_admin()
        self.stdout.write(f"user: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        # several cards may share one app: seed each app once
        for app in dict.fromkeys(feature.app for feature in FEATURES):
            import_module(f"{app}.seed").seed()
            self.stdout.write(f"seeded {app}")
        self.stdout.write(self.style.SUCCESS("Done."))
