"""18.0.1.0.1 security upgrade.

* Rotate every existing woow.service access token. Before this version the
  token was never rotated when a partner was removed from "Shared With", so a
  previously shared partner could still hold a valid chatter token. From now
  on write() rotates it on removal; this closes the window for removals that
  happened before the upgrade. Logged-in portal users are unaffected (their
  access comes from the record rule and a new token is issued on their next
  visit of the detail page).
* Report (do not modify) stored URLs that the new http/https-only constraint
  would reject, so an administrator can correct them.
"""
import logging
import uuid

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("SELECT id FROM woow_service WHERE access_token IS NOT NULL")
    ids = [row[0] for row in cr.fetchall()]
    for service_id in ids:
        cr.execute(
            "UPDATE woow_service SET access_token = %s WHERE id = %s",
            (str(uuid.uuid4()), service_id),
        )
    _logger.info("woow_service_hub: rotated %s service access token(s)", len(ids))

    env = api.Environment(cr, SUPERUSER_ID, {"active_test": False})
    for service in env["woow.service"].search([("url", "!=", False)]):
        try:
            service._check_url_format()
        except ValidationError:
            _logger.warning(
                "woow_service_hub: service %s (id=%s) has a URL that is no "
                "longer accepted (only http/https); please correct it.",
                service.name, service.id,
            )
