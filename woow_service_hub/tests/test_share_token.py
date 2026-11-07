from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import ServiceHubFixtureMixin


@tagged("post_install", "-at_install", "woow_service_hub")
class TestShareTokenRotation(ServiceHubFixtureMixin, TransactionCase):
    """Hardening b373f167d308: un-sharing rotates the portal access token."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_service_hub()
        cls.public_user = cls.env.ref("base.public_user")

    def _token(self):
        return self.service._portal_ensure_token()

    def _public_thread(self, **kwargs):
        return self.env["woow.service"].with_user(self.public_user)._get_thread_with_access(
            self.service.id, "read", **kwargs
        )

    def test_old_token_grants_chatter_access_before_removal(self):
        token = self._token()
        self.assertEqual(self._public_thread(token=token), self.service)

    def test_remove_partner_unlink_command_rotates(self):
        old = self._token()
        pid = self.portal_user.partner_id.id
        old_hash = self.service._sign_token(pid)
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(3, pid)]}
        )
        self.assertTrue(self.service.access_token)
        self.assertNotEqual(self.service.access_token, old)
        self.assertFalse(self._public_thread(token=old),
                         "removed partner's token must no longer open the chatter")
        self.assertFalse(self._public_thread(hash=old_hash, pid=pid),
                         "removed partner's hash/pid must no longer open the chatter")

    def test_replace_command_with_fewer_partners_rotates(self):
        old = self._token()
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(6, 0, [self.other_portal_user.partner_id.id])]}
        )
        self.assertNotEqual(self.service.access_token, old)

    def test_clear_command_rotates(self):
        old = self._token()
        self.service.with_user(self.hub_admin).write({"share_partner_ids": [(5, 0, 0)]})
        self.assertNotEqual(self.service.access_token, old)

    def test_removing_archived_partner_rotates(self):
        old = self._token()
        partner = self.portal_user.partner_id
        self.portal_user.active = False
        partner.active = False
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(3, partner.id)]}
        )
        self.assertNotEqual(self.service.access_token, old)

    def test_adding_partner_keeps_token(self):
        old = self._token()
        extra = self.env["res.partner"].create({"name": "Extra Contact"})
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(4, extra.id)]}
        )
        self.assertEqual(self.service.access_token, old)
        self.assertEqual(self._public_thread(token=old), self.service)

    def test_same_set_and_unrelated_write_keep_token(self):
        old = self._token()
        ids = self.service.share_partner_ids.ids
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(6, 0, ids)], "name": "Renamed"}
        )
        self.service.with_user(self.hub_admin).write({"notes": "x", "color": 3})
        self.assertEqual(self.service.access_token, old)

    def test_multi_record_write_only_rotates_changed(self):
        old_shared = self._token()
        old_private = self.private_service._portal_ensure_token()
        both = (self.service | self.private_service).with_user(self.hub_admin)
        both.write({"share_partner_ids": [(3, self.portal_user.partner_id.id)]})
        self.assertNotEqual(self.service.access_token, old_shared)
        self.assertEqual(self.private_service.access_token, old_private)

    def test_remaining_portal_user_keeps_access(self):
        self._token()
        self.service.with_user(self.hub_admin).write(
            {"share_partner_ids": [(3, self.portal_user.partner_id.id)]}
        )
        thread = self.env["woow.service"].with_user(
            self.other_portal_user
        )._get_thread_with_access(self.service.id, "read")
        self.assertEqual(thread, self.service)
        removed = self.env["woow.service"].with_user(
            self.portal_user
        )._get_thread_with_access(self.service.id, "read")
        self.assertFalse(removed)
