from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import AdminUser

class Command(BaseCommand):
    help = 'Create a college admin user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Admin username')
        parser.add_argument('email', type=str, help='Admin email')
        parser.add_argument('password', type=str, help='Admin password')
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Make this user a Django superuser as well',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        make_superuser = options['superuser']

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User "{username}" already exists!')
                )
                return

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=make_superuser,
                is_superuser=make_superuser
            )

            # Create AdminUser profile
            admin_user = AdminUser.objects.create(
                user=user,
                is_college_admin=True,
                can_scan_qr=True,
                can_manage_participants=True,
                can_manage_events=make_superuser
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created admin user "{username}"!\n'
                    f'Email: {email}\n'
                    f'College Admin: Yes\n'
                    f'Can Scan QR: Yes\n'
                    f'Can Manage Participants: Yes\n'
                    f'Can Manage Events: {"Yes" if make_superuser else "No"}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {str(e)}')
            )
