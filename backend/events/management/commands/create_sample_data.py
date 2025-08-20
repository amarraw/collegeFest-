from django.core.management.base import BaseCommand
from events.models import Event, Participant
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create sample events and participants for testing'

    def handle(self, *args, **options):
        try:
            # Create sample events
            events_data = [
                {
                    'name': 'Tech Fest 2024',
                    'description': 'Annual technology festival showcasing student projects and innovations',
                    'venue': 'Main Auditorium',
                    'date': timezone.now() + timedelta(days=7),
                    'max_participants': 200
                },
                {
                    'name': 'Cultural Night',
                    'description': 'Evening of music, dance, and cultural performances',
                    'venue': 'Open Air Theater',
                    'date': timezone.now() + timedelta(days=14),
                    'max_participants': 300
                },
                {
                    'name': 'Sports Meet',
                    'description': 'Inter-college sports competition',
                    'venue': 'Sports Complex',
                    'date': timezone.now() + timedelta(days=21),
                    'max_participants': 150
                }
            ]

            created_events = []
            for event_data in events_data:
                event, created = Event.objects.get_or_create(
                    name=event_data['name'],
                    defaults=event_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created event: {event.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Event already exists: {event.name}')
                    )
                created_events.append(event)

            # Create sample participants
            participants_data = [
                {'name': 'John Doe', 'email': 'john.doe@email.com', 'phone': '+1234567890'},
                {'name': 'Jane Smith', 'email': 'jane.smith@email.com', 'phone': '+1234567891'},
                {'name': 'Mike Johnson', 'email': 'mike.johnson@email.com', 'phone': '+1234567892'},
                {'name': 'Sarah Wilson', 'email': 'sarah.wilson@email.com', 'phone': '+1234567893'},
                {'name': 'David Brown', 'email': 'david.brown@email.com', 'phone': '+1234567894'},
                {'name': 'Lisa Davis', 'email': 'lisa.davis@email.com', 'phone': '+1234567895'},
                {'name': 'Tom Miller', 'email': 'tom.miller@email.com', 'phone': '+1234567896'},
                {'name': 'Emma Garcia', 'email': 'emma.garcia@email.com', 'phone': '+1234567897'},
            ]

            for i, participant_data in enumerate(participants_data):
                # Assign participants to different events
                event = created_events[i % len(created_events)]
                
                participant, created = Participant.objects.get_or_create(
                    email=participant_data['email'],
                    defaults={
                        'name': participant_data['name'],
                        'phone': participant_data['phone'],
                        'event': event,
                        'otp_code': str(random.randint(100000, 999999)),
                        'otp_verified': random.choice([True, False]),
                        'checked_in': random.choice([True, False])
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created participant: {participant.name} for {event.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Participant already exists: {participant.name}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Sample data created successfully!\n'
                    f'Events: {len(created_events)}\n'
                    f'Participants: {len(participants_data)}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating sample data: {str(e)}')
            )
