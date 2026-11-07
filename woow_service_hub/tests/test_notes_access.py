from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import NOTES_SECRET, ServiceHubFixtureMixin


@tagged("post_install", "-at_install", "woow_service_hub")
class TestNotesFieldAccess(ServiceHubFixtureMixin, TransactionCase):
    """Finding fd6dbca01ff9: portal users must not read Internal Notes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()

    def test_portal_read_notes_raises(self):
        service = self.service.with_user(self.portal_user)
        with self.assertRaises(AccessError):
            service.read(["notes"])

    def test_portal_search_read_notes_raises(self):
        Service = self.env["woow.service"].with_user(self.portal_user)
        with self.assertRaises(AccessError):
            Service.search_read([], ["name", "notes"])

    def test_portal_search_read_default_fields_has_no_notes(self):
        Service = self.env["woow.service"].with_user(self.portal_user)
        rows = Service.search_read([])
        self.assertEqual([r["id"] for r in rows], [self.service.id],
                         "portal still sees only the shared service")
        for row in rows:
            self.assertNotIn("notes", row)
            self.assertNotIn(NOTES_SECRET, repr(row))

    def test_portal_fields_get_hides_notes(self):
        fields_desc = self.env["woow.service"].with_user(self.portal_user).fields_get()
        self.assertNotIn("notes", fields_desc)

    def test_portal_cannot_filter_on_notes(self):
        Service = self.env["woow.service"].with_user(self.portal_user)
        with self.assertRaises(AccessError):
            Service.search([("notes", "ilike", "sk-internal")])

    def test_portal_reads_public_fields(self):
        """Legit portal flow (tests/test_api.py reads name): still allowed."""
        rows = self.service.with_user(self.portal_user).read(
            ["name", "url", "description", "category_ids", "internal_manager_id"]
        )
        self.assertEqual(rows[0]["name"], "Shared Grafana")
        self.assertEqual(rows[0]["url"], "grafana.example.com")

    def test_portal_still_cannot_read_unshared(self):
        with self.assertRaises(AccessError):
            self.private_service.with_user(self.portal_user).read(["name"])

    def test_hub_user_and_admin_read_notes(self):
        for user in (self.hub_user, self.hub_admin):
            rows = self.service.with_user(user).read(["notes"])
            self.assertEqual(rows[0]["notes"], NOTES_SECRET)

    def test_hub_admin_writes_notes(self):
        self.service.with_user(self.hub_admin).write({"notes": "updated"})
        self.assertEqual(self.service.notes, "updated")

    def test_backend_form_view_still_loads_for_hub_user(self):
        Service = self.env["woow.service"].with_user(self.hub_user)
        arch = Service.get_views([(False, "form")])["views"]["form"]["arch"]
        self.assertIn('<field name="notes"', arch)

    def test_portal_form_view_strips_notes(self):
        """Groups-restricted fields are removed from the arch for others."""
        Service = self.env["woow.service"].with_user(self.portal_user)
        arch = Service.get_views([(False, "form")])["views"]["form"]["arch"]
        self.assertNotIn('<field name="notes"', arch)
