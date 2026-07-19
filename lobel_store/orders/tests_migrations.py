from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class OrderSnapshotMigrationTests(TransactionTestCase):
    migrate_from = [
        ("orders", "0005_orderitem_color_name_orderitem_product_name_and_more"),
        ("products", "0007_category_is_active_alter_product_category"),
        ("users", "0002_remove_customer_phone_customer_country_and_more"),
    ]
    migrate_to = [
        ("orders", "0006_order_currency_order_customer_email_and_more"),
        ("products", "0007_category_is_active_alter_product_category"),
        ("users", "0002_remove_customer_phone_customer_country_and_more"),
    ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        User = old_apps.get_model("auth", "User")
        Customer = old_apps.get_model("users", "Customer")
        Category = old_apps.get_model("products", "Category")
        Product = old_apps.get_model("products", "Product")
        ProductVariant = old_apps.get_model("products", "ProductVariant")
        Order = old_apps.get_model("orders", "Order")
        OrderItem = old_apps.get_model("orders", "OrderItem")

        user = User.objects.create(
            username="migration@example.com", email="migration@example.com",
            first_name="Mariam", last_name="Traoré",
        )
        customer = Customer.objects.create(
            user=user, phone_number="+22370000001", address="Bamako", country="ML"
        )
        category = Category.objects.create(name="Historique")
        product = Product.objects.create(
            name="Article", category=category, price=Decimal("500.00")
        )
        variant = ProductVariant.objects.create(product=product, stock=2, sku="HIST-1")
        order = Order.objects.create(customer=customer, complete=True, status="paid")
        OrderItem.objects.create(
            order=order, product=product, variant=variant, quantity=2,
            product_name="Article historique", sku="HIST-1",
            unit_price=Decimal("450.00"),
        )
        self.order_id = order.id

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_order_is_preserved_and_backfilled_from_phase3_snapshots(self):
        Order = self.apps.get_model("orders", "Order")
        OrderItem = self.apps.get_model("orders", "OrderItem")
        order = Order.objects.get(pk=self.order_id)
        item = OrderItem.objects.get(order_id=self.order_id)
        self.assertEqual(item.product_name, "Article historique")
        self.assertEqual(item.unit_price, Decimal("450.00"))
        self.assertEqual(item.subtotal, Decimal("900.00"))
        self.assertEqual(order.total_amount, Decimal("900.00"))
        self.assertEqual(order.customer_name, "Mariam Traoré")
        self.assertIsNotNone(order.snapshot_at)
