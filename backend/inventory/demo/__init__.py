"""Fictional demo data for the public StockFlow demo.

Every name, address, e-mail and phone number here is invented (e-mails use
example.com, phone numbers the reserved 555-01xx range).
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from inventory.models import (
    Category,
    Order,
    OrderItem,
    Product,
    Stock,
    StockMovement,
    Supplier,
    Warehouse,
)
from inventory.services import create_order

MANAGER_GROUP = "Manager"
STAFF_GROUP = "Staff"

CATEGORIES = {
    "Electronics": "Cables, peripherals and small devices.",
    "Office Supplies": "Paper, pens and desk essentials.",
    "Tools": "Hand and power tools for the workshop.",
    "Packaging": "Boxes, tape and protective wrap.",
}

SUPPLIERS = [
    ("Brightwire Components", "orders@brightwire.example.com", "555-0101", "12 Circuit Lane"),
    ("Paperleaf Distribution", "sales@paperleaf.example.com", "555-0102", "88 Quarry Road"),
    ("Ironbark Tool Co.", "hello@ironbark.example.com", "555-0103", "5 Anvil Court"),
    ("Boxwell Packaging", "service@boxwell.example.com", "555-0104", "230 Carton Avenue"),
]

WAREHOUSES = [
    ("Main Warehouse", "Unit 4, Lakeside Industrial Park"),
    ("East Depot", "17 Harbourview Drive"),
]

# (sku, name, category, supplier index, cost, sale, threshold, main qty, east qty)
PRODUCTS = [
    ("DEMO-1001", "Wireless Mouse", "Electronics", 0, "8.40", "14.99", 15, 60, 20),
    ("DEMO-1002", "USB-C Cable (1 m)", "Electronics", 0, "2.10", "6.49", 20, 120, 40),
    ("DEMO-1003", "Mechanical Keyboard", "Electronics", 0, "41.00", "69.00", 10, 12, 4),
    ("DEMO-1004", "24-inch Monitor", "Electronics", 0, "112.50", "169.00", 5, 9, 0),
    ("DEMO-1005", "A4 Paper Ream", "Office Supplies", 1, "3.20", "5.99", 25, 200, 80),
    ("DEMO-1006", "Ballpoint Pens (50 pack)", "Office Supplies", 1, "4.75", "8.99", 15, 14, 30),
    ("DEMO-1007", "Heavy-duty Stapler", "Office Supplies", 1, "6.30", "11.49", 10, 35, 10),
    ("DEMO-1008", "Sticky Notes (12 pads)", "Office Supplies", 1, "3.90", "7.25", 20, 18, 0),
    ("DEMO-1009", "Cordless Drill", "Tools", 2, "54.00", "89.00", 5, 16, 6),
    ("DEMO-1010", "Screwdriver Set", "Tools", 2, "11.20", "19.99", 10, 40, 12),
    ("DEMO-1011", "Measuring Tape (8 m)", "Tools", 2, "4.10", "8.49", 10, 8, 15),
    ("DEMO-1012", "Safety Gloves (pair)", "Tools", 2, "1.60", "3.99", 30, 150, 60),
    ("DEMO-1013", "Shipping Box (medium)", "Packaging", 3, "0.85", "1.99", 50, 400, 150),
    ("DEMO-1014", "Bubble Wrap Roll", "Packaging", 3, "7.40", "12.99", 10, 22, 5),
    ("DEMO-1015", "Packing Tape (6 rolls)", "Packaging", 3, "5.20", "9.49", 15, 13, 25),
    ("DEMO-1016", "Label Printer", "Electronics", 0, "38.00", "59.00", 5, 0, 3),
]

# (customer, warehouse index, [(sku, quantity), ...], note)
ORDERS = [
    ("Quillfeather Stationers", 0, [("DEMO-1005", 20), ("DEMO-1006", 2)], ""),
    ("Bramblewood Cafe", 0, [("DEMO-1013", 60), ("DEMO-1015", 3)], "Weekly packaging"),
    ("Copperkettle Workshop", 0, [("DEMO-1009", 2), ("DEMO-1010", 4)], ""),
    ("Lanternfield Library", 1, [("DEMO-1005", 15), ("DEMO-1007", 2)], ""),
    ("Tidewater Print Studio", 0, [("DEMO-1002", 25), ("DEMO-1001", 6)], ""),
    ("Bramblewood Cafe", 1, [("DEMO-1012", 10)], ""),
    ("Hollowbrook Makerspace", 0, [("DEMO-1003", 3), ("DEMO-1011", 2)], "Pick-up"),
    ("Quillfeather Stationers", 0, [("DEMO-1008", 6), ("DEMO-1014", 4)], ""),
]


def ensure_demo_mode() -> None:
    if not settings.DEMO_MODE:
        raise ImproperlyConfigured(
            "DEMO_MODE is off: the demo commands only run on a demo database (set DEMO_MODE=True)."
        )


def ensure_groups() -> tuple[Group, Group]:
    manager, _ = Group.objects.get_or_create(name=MANAGER_GROUP)
    staff, _ = Group.objects.get_or_create(name=STAFF_GROUP)
    return manager, staff


def ensure_demo_user() -> User:
    """Create or refresh the shared demo login (manager role, no admin access)."""
    password = settings.DEMO_PASSWORD
    if len(password) < 8:
        raise ImproperlyConfigured("DEMO_PASSWORD must be set (at least 8 characters).")
    manager, _ = ensure_groups()
    user, _ = User.objects.get_or_create(
        username=settings.DEMO_USERNAME,
        defaults={"first_name": "Demo", "last_name": "Manager", "email": "demo@example.com"},
    )
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.set_password(password)
    user.save()
    user.groups.set([manager])
    return user


@transaction.atomic
def seed(*, with_demo_user: bool = True) -> dict[str, int]:
    """Load the demo data. Idempotent: existing records are kept, nothing is
    duplicated, and orders are only created on an empty order book."""
    ensure_groups()
    if with_demo_user:
        ensure_demo_user()

    categories = {
        name: Category.objects.get_or_create(name=name, defaults={"description": desc})[0]
        for name, desc in CATEGORIES.items()
    }
    suppliers = [
        Supplier.objects.get_or_create(
            name=name, defaults={"email": email, "phone": phone, "address": address}
        )[0]
        for name, email, phone, address in SUPPLIERS
    ]
    warehouses = [
        Warehouse.objects.get_or_create(name=name, defaults={"location": location})[0]
        for name, location in WAREHOUSES
    ]

    products = {}
    for sku, name, cat, sup, cost, sale, threshold, main_qty, east_qty in PRODUCTS:
        product, _ = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "name": name,
                "category": categories[cat],
                "supplier": suppliers[sup],
                "cost_price": Decimal(cost),
                "sale_price": Decimal(sale),
                "reorder_threshold": threshold,
            },
        )
        products[sku] = product
        for warehouse, qty in zip(warehouses, (main_qty, east_qty), strict=True):
            if Stock.objects.filter(product=product, warehouse=warehouse).exists():
                continue
            if qty:
                StockMovement.objects.create(
                    product=product,
                    warehouse=warehouse,
                    movement_type=StockMovement.MovementType.IN,
                    quantity=qty,
                    note="Opening stock (demo)",
                )
            else:
                Stock.objects.create(product=product, warehouse=warehouse, quantity=0)

    if not Order.objects.exists():
        for customer, wh_index, lines, note in ORDERS:
            create_order(
                warehouse=warehouses[wh_index],
                customer_name=customer,
                items=[{"product": products[sku], "quantity": qty} for sku, qty in lines],
                note=note,
            )

    cache.clear()
    return {
        "products": Product.objects.count(),
        "warehouses": Warehouse.objects.count(),
        "movements": StockMovement.objects.count(),
        "orders": Order.objects.count(),
    }


@transaction.atomic
def reset() -> dict[str, int]:
    """Delete every inventory record and every non-superuser account except the
    demo login, then seed again. Superusers (the operator's own) are kept."""
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    # Queryset deletes bypass StockMovement.delete(), which refuses single deletes.
    StockMovement.objects.all().delete()
    Stock.objects.all().delete()
    Product.objects.all().delete()
    Supplier.objects.all().delete()
    Warehouse.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(is_superuser=False).exclude(username=settings.DEMO_USERNAME).delete()
    return seed()
