import importlib.util
import os

from odoo.modules.module import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import ServiceHubFixtureMixin


def _load_migration():
    path = os.path.join(
        get_module_path("woow_service_hub"),
        "migrations", "18.0.1.1.0", "pre-migrate.py",
    )
    spec = importlib.util.spec_from_file_location("woow_service_hub_mig_18_0_1_1_0", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manager_foreign_key_targets(cr):
    cr.execute("""
        SELECT c.confrelid::regclass::text
          FROM pg_constraint c
          JOIN pg_attribute a
            ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
         WHERE c.contype = 'f'
           AND c.conrelid = 'woow_service'::regclass
           AND a.attname = 'internal_manager_id'
    """)
    return [row[0] for row in cr.fetchall()]


@tagged("post_install", "-at_install", "woow_service_hub")
class TestInternalManager(ServiceHubFixtureMixin, TransactionCase):
    """Internal Manager is an internal user; the module does not need hr."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()

    def test_module_does_not_depend_on_hr(self):
        module = self.env["ir.module.module"].search([("name", "=", "woow_service_hub")])
        self.assertNotIn("hr", module.dependencies_id.mapped("name"))

    def test_manager_is_an_internal_user(self):
        field = self.env["woow.service"]._fields["internal_manager_id"]
        self.assertEqual(field.comodel_name, "res.users")
        self.assertEqual(_manager_foreign_key_targets(self.env.cr), ["res_users"])
        candidates = self.env["res.users"].search(field.domain)
        self.assertIn(self.hub_user, candidates)
        self.assertNotIn(self.portal_user, candidates, "portal users are not offered")

        self.service.with_user(self.hub_admin).write({"internal_manager_id": self.hub_user.id})
        self.assertEqual(self.service.internal_manager_id, self.hub_user)
        row = self.service.with_user(self.portal_user).read(["internal_manager_id"])[0]
        self.assertEqual(row["internal_manager_id"], (self.hub_user.id, "Svc Hub User"))

    def test_pre_migrate_maps_employees_to_users(self):
        cr = self.env.cr
        # Rebuild the 18.0.1.0.1 shape: the column holds hr_employee ids.
        if "hr.employee" in self.env:
            Employee = self.env["hr.employee"]
            employee_with_user = Employee.create({"name": "Mapped Manager", "user_id": self.hub_user.id}).id
            employee_without_user = Employee.create({"name": "No Account"}).id
        else:
            cr.execute("CREATE TABLE hr_employee (id int PRIMARY KEY, name varchar, user_id int)")
            employee_with_user, employee_without_user = 900001, 900002
            cr.execute(
                "INSERT INTO hr_employee VALUES (%s, 'Mapped Manager', %s), (%s, 'No Account', NULL)",
                (employee_with_user, self.hub_user.id, employee_without_user),
            )
        cr.execute("UPDATE woow_service SET internal_manager_id = NULL")
        cr.execute("ALTER TABLE woow_service DROP CONSTRAINT IF EXISTS woow_service_internal_manager_id_fkey")
        cr.execute("""
            ALTER TABLE woow_service ADD CONSTRAINT woow_service_internal_manager_id_fkey
            FOREIGN KEY (internal_manager_id) REFERENCES hr_employee (id) ON DELETE SET NULL
        """)
        cr.execute("UPDATE woow_service SET internal_manager_id = %s WHERE id = %s",
                   (employee_with_user, self.service.id))
        cr.execute("UPDATE woow_service SET internal_manager_id = %s WHERE id = %s",
                   (employee_without_user, self.private_service.id))
        self.env.invalidate_all()

        migration = _load_migration()
        with self.assertLogs("woow_service_hub_mig_18_0_1_1_0", level="INFO") as logs:
            migration.migrate(cr, "18.0.1.0.1")
        migration.migrate(cr, "18.0.1.0.1")  # re-run: values are user ids now, left alone
        self.env.invalidate_all()

        self.assertEqual(self.service.internal_manager_id, self.hub_user)
        self.assertFalse(self.private_service.internal_manager_id)
        self.assertTrue(any("Private Vault" in line and "WARNING" in line for line in logs.output))
        self.assertEqual(_manager_foreign_key_targets(cr), [], "foreign key to hr_employee dropped")

    def test_fresh_install_noop(self):
        self.service.internal_manager_id = self.hub_user
        _load_migration().migrate(self.env.cr, None)
        self.env.invalidate_all()
        self.assertEqual(self.service.internal_manager_id, self.hub_user)
        self.assertEqual(_manager_foreign_key_targets(self.env.cr), ["res_users"])
