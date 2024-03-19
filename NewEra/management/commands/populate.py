from django.core.management.base import BaseCommand
from NewEra.models import User

# POPULATE SCRIPT

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to create sample users.'

    def _create_users(self):
        """
        sow = User.objects.create_user(username='sow', password='sow', first_name='Max', last_name='K', email='mkornyev@gmail.com')
        sow.is_superuser = False
        sow.save()
        """
        admin = User.objects.create_user(username='admintaili', password='gy!e12uNAs', first_name='Taili', last_name='Thompson', email='bvbaseball42@gmail.com')
        admin.is_superuser = True
        admin.save()
        
    def handle(self, *args, **options):
        self._create_users()
