"""
Management command to seed default emergency cards.

Run with: python manage.py seed_emergency_cards
"""

from django.core.management.base import BaseCommand
from sos.models import EmergencyCard


# Default emergency cards for quick-tap selection
DEFAULT_CARDS = [
    {
        'code': 'heart_attack',
        'name': 'Heart Attack',
        'icon': '🫀',
        'category': 'medical',
        'urgency_boost': 30,
        'keywords': ['heart', 'attack', 'chest', 'pain', 'cardiac', 'pulse'],
        'display_order': 1,
    },
    {
        'code': 'breathing_problem',
        'name': 'Breathing Problem',
        'icon': '🫁',
        'category': 'medical',
        'urgency_boost': 25,
        'keywords': ['breathing', 'asthma', 'choking', 'suffocating', 'oxygen'],
        'display_order': 2,
    },
    {
        'code': 'road_accident',
        'name': 'Road Accident',
        'icon': '🚗',
        'category': 'accident',
        'urgency_boost': 25,
        'keywords': ['car', 'crash', 'accident', 'collision', 'vehicle', 'road', 'traffic'],
        'display_order': 3,
    },
    {
        'code': 'fire_explosion',
        'name': 'Fire / Explosion',
        'icon': '🔥',
        'category': 'accident',
        'urgency_boost': 30,
        'keywords': ['fire', 'explosion', 'smoke', 'burning', 'flames', 'gas'],
        'display_order': 4,
    },
    {
        'code': 'suicide_selfharm',
        'name': 'Suicide / Self-Harm',
        'icon': '🆘',
        'category': 'emotional',
        'urgency_boost': 35,
        'keywords': ['suicide', 'self-harm', 'depressed', 'hopeless', 'end', 'life'],
        'display_order': 5,
    },
    {
        'code': 'violence_assault',
        'name': 'Violence / Assault',
        'icon': '👊',
        'category': 'safety',
        'urgency_boost': 25,
        'keywords': ['attack', 'assault', 'violence', 'threat', 'abuse', 'fight'],
        'display_order': 6,
    },
    {
        'code': 'poisoning_overdose',
        'name': 'Poisoning / Overdose',
        'icon': '💊',
        'category': 'medical',
        'urgency_boost': 30,
        'keywords': ['poison', 'overdose', 'drugs', 'pills', 'toxic', 'ingested'],
        'display_order': 7,
    },
    {
        'code': 'injury_bleeding',
        'name': 'Injury / Bleeding',
        'icon': '🤕',
        'category': 'medical',
        'urgency_boost': 20,
        'keywords': ['injury', 'bleeding', 'blood', 'wound', 'cut', 'broken', 'fracture'],
        'display_order': 8,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with default emergency cards for quick-tap selection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing cards',
        )

    def handle(self, *args, **options):
        force = options['force']
        created_count = 0
        updated_count = 0
        
        self.stdout.write(self.style.NOTICE('Seeding emergency cards...'))
        
        for card_data in DEFAULT_CARDS:
            code = card_data['code']
            
            if force:
                # Update or create
                card, created = EmergencyCard.objects.update_or_create(
                    code=code,
                    defaults=card_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  [+] Created: {card.code} ({card.name})")
                else:
                    updated_count += 1
                    self.stdout.write(f"  [~] Updated: {card.code}")
            else:
                # Only create if doesn't exist
                card, created = EmergencyCard.objects.get_or_create(
                    code=code,
                    defaults=card_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  [+] Created: {card.code} ({card.name})")
                else:
                    self.stdout.write(f"  [-] Exists: {card.code}")
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Updated: {updated_count}'
        ))
