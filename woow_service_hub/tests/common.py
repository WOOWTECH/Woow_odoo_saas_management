from odoo.tests.common import new_test_user

NOTES_SECRET = "vendor account id 42 / api key sk-internal-only"


class ServiceHubFixtureMixin:
    """Shared fixture: one service shared with a portal user, one not."""

    @classmethod
    def _setup_service_hub(cls):
        env = cls.env
        cls.portal_user = new_test_user(
            env, login="svc_portal", groups="base.group_portal",
            name="Svc Portal", password="svc_portal_pwd_123",
        )
        cls.other_portal_user = new_test_user(
            env, login="svc_portal2", groups="base.group_portal",
            name="Svc Portal Two", password="svc_portal2_pwd_123",
        )
        cls.hub_user = new_test_user(
            env, login="svc_hub_user",
            groups="base.group_user,woow_service_hub.woow_service_hub_group_user",
            name="Svc Hub User",
        )
        cls.hub_admin = new_test_user(
            env, login="svc_hub_admin",
            groups="base.group_user,woow_service_hub.woow_service_hub_group_admin",
            name="Svc Hub Admin",
        )
        Service = env["woow.service"].with_user(cls.hub_admin)
        cls.service = Service.create({
            "name": "Shared Grafana",
            "url": "grafana.example.com",
            "description": "<p>Public description</p>",
            "notes": NOTES_SECRET,
            "share_partner_ids": [(6, 0, [
                cls.portal_user.partner_id.id,
                cls.other_portal_user.partner_id.id,
            ])],
        })
        cls.private_service = Service.create({
            "name": "Private Vault",
            "url": "https://vault.example.com",
            "notes": NOTES_SECRET,
        })
