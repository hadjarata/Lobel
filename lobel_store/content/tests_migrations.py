from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class HomeHeroSimplificationMigrationTests(TransactionTestCase):
    migrate_from = [("content", "0002_customdressservice")]
    migrate_to = [("content", "0003_simplify_homehero")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        HomeHero = old_apps.get_model("content", "HomeHero")

        HomeHero.objects.create(
            title="Ancienne image",
            description="Configuration inactive",
            media_type="IMAGE",
            desktop_image="content/home-hero/old-image.jpg",
            mobile_image="content/home-hero/old-mobile.jpg",
            is_active=False,
        )
        selected = HomeHero.objects.create(
            title="Vidéo active",
            description="Configuration à préserver",
            media_type="VIDEO",
            desktop_image="content/home-hero/old-poster.jpg",
            video="content/home-hero/hero.mp4",
            video_poster="content/home-hero/old-poster.jpg",
            is_active=True,
        )
        self.selected_id = selected.pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_preserves_one_preferred_configuration_and_its_primary_media(self):
        HomeHero = self.apps.get_model("content", "HomeHero")
        self.assertEqual(HomeHero.objects.count(), 1)
        hero = HomeHero.objects.get()
        self.assertEqual(hero.pk, self.selected_id)
        self.assertEqual(hero.title, "Vidéo active")
        self.assertEqual(hero.description, "Configuration à préserver")
        self.assertEqual(hero.media_type, "VIDEO")
        self.assertEqual(hero.video.name, "content/home-hero/hero.mp4")
        self.assertFalse(hero.image)
