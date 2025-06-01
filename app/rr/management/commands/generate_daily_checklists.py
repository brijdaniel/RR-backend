from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from rr.models import User, Checklist

class Command(BaseCommand):
    help = 'Generates a new checklist for each active user for the current day'

    def handle(self, *args, **options):
        today = timezone.now()
        active_users = User.objects.filter(is_active=True)
        checklists_created = 0

        with transaction.atomic():
            for user in active_users:
                # Check if user already has a checklist for today
                existing_checklist = Checklist.objects.filter(
                    user=user,
                    created_at__date=today.date()
                ).exists()

                if not existing_checklist:
                    Checklist.objects.create(user=user)
                    checklists_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {checklists_created} new checklists'
            )
        ) 