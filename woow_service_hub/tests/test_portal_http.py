from odoo.tests import tagged
from odoo.tests.common import HttpCase, JsonRpcException

from .common import NOTES_SECRET, ServiceHubFixtureMixin


@tagged("post_install", "-at_install", "woow_service_hub")
class TestPortalPages(ServiceHubFixtureMixin, HttpCase):
    """Portal pages keep rendering; JSON-RPC cannot leak notes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()

    def setUp(self):
        super().setUp()
        self.authenticate("svc_portal", "svc_portal_pwd_123")

    def _call_kw(self, method, args, kwargs=None):
        return self.make_jsonrpc_request("/web/dataset/call_kw", {
            "model": "woow.service",
            "method": method,
            "args": args,
            "kwargs": kwargs or {},
        })

    def test_my_services_list_renders(self):
        res = self.url_open("/my/services")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Shared Grafana", res.text)
        self.assertNotIn("Private Vault", res.text)
        self.assertNotIn(NOTES_SECRET, res.text)

    def test_my_service_detail_renders_without_notes(self):
        res = self.url_open(f"/my/services/{self.service.id}")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Shared Grafana", res.text)
        self.assertIn("Public description", res.text)
        self.assertNotIn(NOTES_SECRET, res.text)

    def test_unshared_detail_redirects(self):
        res = self.url_open(f"/my/services/{self.private_service.id}", allow_redirects=False)
        self.assertIn(res.status_code, (302, 303))

    def test_rpc_read_name_ok(self):
        rows = self._call_kw("search_read", [[], ["name"]])
        self.assertEqual([r["name"] for r in rows], ["Shared Grafana"])

    def test_rpc_read_notes_denied(self):
        with self.assertRaises(JsonRpcException) as cm:
            self._call_kw("read", [[self.service.id], ["notes"]])
        self.assertIn("AccessError", str(cm.exception))

    def test_rpc_search_read_all_fields_has_no_notes(self):
        rows = self._call_kw("search_read", [[]])
        self.assertTrue(rows)
        for row in rows:
            self.assertNotIn("notes", row)
        self.assertNotIn(NOTES_SECRET, repr(rows))
