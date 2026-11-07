from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import ServiceHubFixtureMixin

REJECTED = [
    "ftp://files.example.com/pub",
    "FTP://files.example.com",
    "mailto:ops@example.com",
    "file:///etc/passwd",
    "tel:+886212345678",
    "ssh://git@example.com",
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "java\tscript:alert(1)",
    "javascript:1/alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
    "http:example.com",
    "//evil.example.com",
    "not a url",
]

ACCEPTED = [
    "woowtech.slack.com",
    "github.com/woowtech",
    "localhost:9103",
    "grafana.local:3000/d/abc?orgId=1#panel",
    "192.168.1.10:8080",
    "http://example.com",
    "https://example.com/path?q=a:b",
    "HTTPS://Example.com",
    "Http://example.com:8443/x",
]


@tagged("post_install", "-at_install", "woow_service_hub")
class TestUrlSchemeWhitelist(ServiceHubFixtureMixin, TransactionCase):
    """Hardening f18fc63d5864: only http/https (or bare host) URLs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()
        cls.Service = cls.env["woow.service"].with_user(cls.hub_admin)

    def test_create_rejects_non_http_schemes(self):
        for url in REJECTED:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                with self.env.cr.savepoint():
                    self.Service.create({"name": "Bad", "url": url})

    def test_write_rejects_non_http_schemes(self):
        for url in REJECTED:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                with self.env.cr.savepoint():
                    self.service.with_user(self.hub_admin).write({"url": url})
        self.assertEqual(self.service.url, "grafana.example.com")

    def test_accepts_http_https_and_bare_hosts(self):
        for url in ACCEPTED:
            with self.subTest(url=url):
                rec = self.Service.create({"name": "Good", "url": url})
                self.assertEqual(rec.url, url)
                self.assertTrue(rec.get_full_url().lower().startswith(("http://", "https://")))

    def test_empty_url_allowed(self):
        rec = self.Service.create({"name": "No URL"})
        self.assertEqual(rec.get_full_url(), "")
        rec.write({"url": False})

    def test_get_full_url(self):
        cases = {
            "woowtech.slack.com": "https://woowtech.slack.com",
            "localhost:9103": "https://localhost:9103",
            "http://example.com": "http://example.com",
            "  https://example.com  ": "https://example.com",
            "HTTPS://Example.com": "HTTPS://Example.com",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                rec = self.Service.create({"name": "U", "url": raw})
                self.assertEqual(rec.get_full_url(), expected)

    def test_action_open_service(self):
        action = self.service.with_user(self.hub_user).action_open_service()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], "https://grafana.example.com")

    def test_demo_data_urls_still_valid(self):
        """Every URL shipped in demo data must pass the stricter check."""
        from lxml import etree

        from odoo.tools import file_open

        with file_open("woow_service_hub/demo/demo_data.xml", "rb") as fh:
            tree = etree.parse(fh)
        urls = [n.text for n in tree.xpath("//record[@model='woow.service']/field[@name='url']")]
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.Service.create({"name": "Demo", "url": url})
