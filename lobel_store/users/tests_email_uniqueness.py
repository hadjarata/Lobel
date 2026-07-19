from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth.models import User
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase

from .services import normalize_email


class EmailUniquenessTests(TestCase):
    def test_normalization_is_conservative(self):
        self.assertEqual(normalize_email("  A.B+tag@EXAMPLE.COM "), "A.B+tag@example.com")

    def test_database_rejects_case_insensitive_duplicate(self):
        User.objects.create_user("one", "User@Test.com", "Strong!Password-2026")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("two", "user@test.com", "Strong!Password-2026")


class ConcurrentEmailUniquenessTests(TransactionTestCase):
    reset_sequences = True

    @staticmethod
    def create_user(username, email):
        close_old_connections()
        try:
            User.objects.create_user(username, email, "Strong!Password-2026")
            return "created"
        except IntegrityError:
            return "conflict"
        finally:
            close_old_connections()

    def test_concurrent_case_variants_create_only_one_account(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda args: self.create_user(*args),
                [("race-one", "User@Test.com"), ("race-two", "user@test.com")],
            ))
        self.assertCountEqual(results, ["created", "conflict"])
        self.assertEqual(User.objects.filter(email__iexact="user@test.com").count(), 1)
