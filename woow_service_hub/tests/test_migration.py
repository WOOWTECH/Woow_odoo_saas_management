import importlib.util
import os

from odoo.modules.module import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import ServiceHubFixtureMixin


def _load_migration():
    path = os.path.join(
        get_module_path("woow_service_hub"),
        "migrations", "18.0.1.0.1", "post-migrate.py",
    )
    spec = importlib.util.spec_from_file_location("woow_service_hub_mig_18_0_1_0_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install", "woow_service_hub")
class TestMigration180101(ServiceHubFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()

    def test_rotates_existing_tokens_and_reports_bad_urls(self):
        old = self.service._portal_ensure_token()
        self.assertFalse(self.private_service.access_token)
        # legacy value stored before the whitelist existed
        self.env.cr.execute(
            "UPDATE woow_service SET url = 'ftp://legacy.example.com' WHERE id = %s",
            (self.private_service.id,),
        )
        self.env.invalidate_all()
        migration = _load_migration()
        with self.assertLogs("woow_service_hub_mig_18_0_1_0_1", level="INFO") as logs:
            migration.migrate(self.env.cr, "18.0.1.0.0")
            migration.migrate(self.env.cr, "18.0.1.0.0")  # re-run is harmless
        self.env.invalidate_all()
        self.assertTrue(self.service.access_token)
        self.assertNotEqual(self.service.access_token, old)
        self.assertFalse(self.private_service.access_token, "no token -> none created")
        self.assertEqual(self.private_service.url, "ftp://legacy.example.com",
                         "migration reports but never rewrites URLs")
        self.assertTrue(any("Private Vault" in line and "WARNING" in line for line in logs.output))

    def test_fresh_install_noop(self):
        old = self.service._portal_ensure_token()
        _load_migration().migrate(self.env.cr, None)
        self.env.invalidate_all()
        self.assertEqual(self.service.access_token, old)
