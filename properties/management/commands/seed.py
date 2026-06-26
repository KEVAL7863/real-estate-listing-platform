"""Populate the database with demo users and properties.

Usage: python manage.py seed
"""
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from properties.models import Property, PropertyType, ListingType

User = get_user_model()

CITIES = [
    ("Mumbai", "Maharashtra"), ("Bengaluru", "Karnataka"), ("Pune", "Maharashtra"),
    ("Ahmedabad", "Gujarat"), ("Delhi", "Delhi"), ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"), ("Jaipur", "Rajasthan"),
]

TITLES = [
    "Spacious {bhk}BHK {type} with City View",
    "Modern {bhk}BHK {type} near Metro Station",
    "Luxury {bhk}BHK {type} in Prime Location",
    "Affordable {bhk}BHK {type} for Family",
    "Premium {bhk}BHK {type} with Garden",
    "Cozy {bhk}BHK {type} close to IT Park",
    "Elegant {bhk}BHK {type} with Balcony",
    "Brand New {bhk}BHK {type} Ready to Move",
]

DESC = (
    "A beautiful and well-maintained property in a peaceful neighbourhood. "
    "Close to schools, hospitals, shopping malls and public transport. "
    "Features 24x7 security, power backup, water supply and ample natural light. "
    "Ideal for families and professionals looking for comfort and convenience.\n\n"
    "Contact the owner today to schedule a visit!"
)


class Command(BaseCommand):
    help = "Seed the database with demo users and property listings."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # --- Admin ---
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@estatehub.com",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  Created admin / admin123"))

        # --- Owners ---
        owners = []
        for i in range(1, 4):
            owner, created = User.objects.get_or_create(
                username=f"owner{i}",
                defaults={"email": f"owner{i}@estatehub.com", "role": User.Role.OWNER},
            )
            if created:
                owner.set_password("owner123")
                owner.save()
            owners.append(owner)

        # --- Buyer ---
        buyer, created = User.objects.get_or_create(
            username="buyer1",
            defaults={"email": "buyer1@estatehub.com", "role": User.Role.BUYER},
        )
        if created:
            buyer.set_password("buyer123")
            buyer.save()

        self.stdout.write(self.style.SUCCESS("  Owners: owner1/2/3 (pw owner123), Buyer: buyer1 (pw buyer123)"))

        # --- Properties ---
        types = [c[0] for c in PropertyType.choices]
        type_labels = dict(PropertyType.choices)
        created_count = 0
        for n in range(24):
            city, state = random.choice(CITIES)
            ptype = random.choice(types)
            bhk = random.randint(1, 4)
            listing = random.choice([ListingType.SALE, ListingType.RENT])
            title = random.choice(TITLES).format(bhk=bhk, type=type_labels[ptype])

            if listing == ListingType.RENT:
                price = random.randint(8, 80) * 1000
            else:
                price = random.randint(25, 350) * 100000

            prop = Property(
                owner=random.choice(owners),
                title=title,
                description=DESC,
                property_type=ptype,
                listing_type=listing,
                price=price,
                area_sqft=random.randint(450, 3200),
                bedrooms=bhk,
                bathrooms=random.randint(1, 3),
                address=f"{random.randint(1, 99)}, {random.choice(['Green', 'Park', 'Lake', 'Sun', 'Royal'])} {random.choice(['Residency', 'Heights', 'Towers', 'Enclave'])}",
                city=city,
                state=state,
                pincode=str(random.randint(100000, 999999)),
                has_parking=random.choice([True, False]),
                is_furnished=random.choice([True, False]),
                status=Property.Status.APPROVED if n < 20 else Property.Status.PENDING,
                is_featured=n < 6,
                views=random.randint(5, 500),
            )
            prop.save()
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"  Created {created_count} properties (20 approved, 4 pending)."))
        self.stdout.write(self.style.SUCCESS("Done! Run the server and log in."))
