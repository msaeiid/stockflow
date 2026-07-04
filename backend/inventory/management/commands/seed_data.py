import random

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import (
    Category,
    Product,
    StockMovement,
    Supplier,
    Warehouse,
)
from inventory.services import create_order


class Command(BaseCommand):
    help = "Seed the database with sample data for the demo."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        categories = [
            Category.objects.get_or_create(name=name)[0]
            for name in ["Electronics", "Office Supplies", "Tools", "Packaging"]
        ]

        suppliers = [
            Supplier.objects.get_or_create(
                name=name, defaults={"email": f"{name.lower().replace(' ', '')}@example.com"}
            )[0]
            for name in ["Acme Corp", "Global Traders", "TechSource", "BulkMart"]
        ]

        warehouses = [
            Warehouse.objects.get_or_create(name=name, defaults={"location": loc})[0]
            for name, loc in [
                ("Main Warehouse", "Toronto, ON"),
                ("West Depot", "Vancouver, BC"),
            ]
        ]

        product_names = [
            ("Wireless Mouse", "Electronics"),
            ("USB-C Cable", "Electronics"),
            ("Mechanical Keyboard", "Electronics"),
            ("HD Monitor", "Electronics"),
            ("A4 Paper Ream", "Office Supplies"),
            ("Ballpoint Pens (50pk)", "Office Supplies"),
            ("Stapler", "Office Supplies"),
            ("Sticky Notes", "Office Supplies"),
            ("Cordless Drill", "Tools"),
            ("Screwdriver Set", "Tools"),
            ("Measuring Tape", "Tools"),
            ("Safety Gloves", "Tools"),
            ("Shipping Box (M)", "Packaging"),
            ("Bubble Wrap Roll", "Packaging"),
            ("Packing Tape", "Packaging"),
        ]

        cat_map = {c.name: c for c in categories}
        products = []
        for i, (name, cat_name) in enumerate(product_names):
            cost = round(random.uniform(5, 120), 2)
            product, _ = Product.objects.get_or_create(
                sku=f"SKU-{1000 + i}",
                defaults={
                    "name": name,
                    "category": cat_map[cat_name],
                    "supplier": random.choice(suppliers),
                    "cost_price": cost,
                    "sale_price": round(cost * random.uniform(1.3, 1.8), 2),
                    "reorder_threshold": random.choice([10, 15, 20]),
                },
            )
            products.append(product)

        main_wh = warehouses[0]
        for product in products:
            qty = random.choice([5, 8, 25, 40, 60, 100])  # some intentionally low
            StockMovement.objects.create(
                product=product,
                warehouse=main_wh,
                movement_type=StockMovement.MovementType.IN,
                quantity=qty,
                note="Initial stock (seed)",
            )

        customers = ["Northwind Ltd", "Contoso Inc", "Fabrikam", "Adventure Works"]
        for _ in range(6):
            chosen = random.sample(products, k=random.randint(1, 3))
            items = []
            for p in chosen:
                items.append({"product": p, "quantity": random.randint(1, 3)})
            try:
                create_order(
                    warehouse=main_wh,
                    customer_name=random.choice(customers),
                    items=items,
                )
            except Exception:
                pass  # skip if a product happened to be out of stock

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {Product.objects.count()} products, "
                f"{Warehouse.objects.count()} warehouses, "
                f"{StockMovement.objects.count()} movements."
            )
        )
