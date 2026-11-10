import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.test import SimpleTestCase
from django.core.exceptions import ImproperlyConfigured
from config.environment import load_environment, apply_deployment_settings


class EnvironmentFileTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def test_development_legacy_fallback_and_selected_file_precedence(self):
        self.write(".env", "DB_NAME=legacy\n")
        with patch.dict(os.environ, {}, clear=True):
            selected = load_environment(self.root)
            self.assertEqual(selected.name, "development")
            self.assertEqual(os.environ["DB_NAME"], "legacy")
        self.write(".env.development", "DB_NAME=development\n")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(load_environment(self.root).path.name, ".env.development")
            self.assertEqual(os.environ["DB_NAME"], "development")

    def test_production_never_inherits_legacy_file(self):
        self.write(".env", "DB_NAME=wrong_database\nDB_PASSWORD=wrong_password\n")
        self.write(".env.production", "DB_NAME=production_database\n")
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            selected = load_environment(self.root)
            self.assertEqual(selected.name, "production")
            self.assertEqual(os.environ["DB_NAME"], "production_database")
            self.assertNotIn("DB_PASSWORD", os.environ)

    def test_system_environment_wins(self):
        self.write(".env.testing", "DB_NAME=file_database\n")
        with patch.dict(os.environ, {"APP_ENV": "testing", "DB_NAME": "process_database"}, clear=True):
            self.assertEqual(load_environment(self.root).name, "testing")
            self.assertEqual(os.environ["DB_NAME"], "process_database")

    def test_missing_and_invalid_environment_fail_closed(self):
        self.write(".env", "DB_NAME=development\n")
        for name in ("production", "testing", "../other"):
            with patch.dict(os.environ, {"APP_ENV": name}, clear=True):
                with self.assertRaises(ImproperlyConfigured):
                    load_environment(self.root)

    def test_explicit_file_is_relative_to_project_and_must_exist(self):
        self.write("custom.env", "DB_NAME=custom\n")
        with patch.dict(os.environ, {"APP_ENV": "testing", "DJANGO_ENV_FILE": "custom.env"}, clear=True):
            self.assertEqual(load_environment(self.root).path, self.root / "custom.env")
            self.assertEqual(os.environ["DB_NAME"], "custom")
        with patch.dict(os.environ, {"DJANGO_ENV_FILE": "missing.env"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                load_environment(self.root)

    def test_file_cannot_silently_change_selector(self):
        self.write(".env.development", "APP_ENV=production\n")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                load_environment(self.root)

    def test_production_guard_and_https_configuration(self):
        values = {"DJANGO_ALLOWED_HOSTS": "example.com,localhost", "DJANGO_SECRET_KEY": "a" * 50, "DB_NAME": "production", "DB_USER": "app", "DB_HOST": "127.0.0.1", "DB_PORT": "3306", "DJANGO_DEBUG": "1", "DJANGO_HTTPS": "1", "DJANGO_CSRF_TRUSTED_ORIGINS": "https://example.com"}
        with patch.dict(os.environ, values, clear=True):
            namespace = {"DEBUG": True}
            apply_deployment_settings(namespace, "production")
            self.assertFalse(namespace["DEBUG"])
            self.assertEqual(namespace["ALLOWED_HOSTS"], ["example.com", "localhost"])
            self.assertTrue(namespace["LANGUAGE_COOKIE_SECURE"])
            self.assertTrue(namespace["SECURE_SSL_REDIRECT"])
        with patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": "*"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                apply_deployment_settings({}, "production")

    def test_testing_requires_explicit_database_name(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                apply_deployment_settings({}, "testing")

    def test_production_rejects_placeholder_secret_and_missing_database(self):
        values = {"DJANGO_ALLOWED_HOSTS": "example.com", "DJANGO_SECRET_KEY": "replace-with-a-new-random-secret-of-at-least-32-characters"}
        with patch.dict(os.environ, values, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                apply_deployment_settings({}, "production")
        values["DJANGO_SECRET_KEY"] = "a" * 50
        with patch.dict(os.environ, values, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                apply_deployment_settings({}, "production")
