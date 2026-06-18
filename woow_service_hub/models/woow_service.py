import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class WoowService(models.Model):
    _name = "woow.service"
    _description = "Service"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "name"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name = fields.Char(string="Service Name", required=True, tracking=True)
    logo = fields.Image(string="Logo", max_width=256, max_height=256)
    color = fields.Integer(string="Card Color")

    # ------------------------------------------------------------------
    # Category tags
    # ------------------------------------------------------------------
    category_ids = fields.Many2many(
        comodel_name="woow.service.category",
        relation="woow_service_category_rel",
        column1="service_id",
        column2="category_id",
        string="Categories",
    )

    # ------------------------------------------------------------------
    # URL / launch
    # ------------------------------------------------------------------
    url = fields.Char(string="Service URL")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("url")
    def _check_url_format(self):
        """Validate that the url field contains a well-formed URL.

        Accepts http://, https://, or bare hostnames (which get
        https:// prepended by get_full_url()). Blocks dangerous
        schemes (javascript:, data:, vbscript:) and clearly
        malformed values.
        """
        _url_re = re.compile(
            r"^(https?://)?"           # optional scheme
            r"[a-zA-Z0-9]"            # must start with alnum
            r"[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$"  # rest of URL
        )
        _dangerous_schemes = ("javascript:", "data:", "vbscript:")
        for rec in self:
            if not rec.url:
                continue
            url_stripped = rec.url.strip()
            url_lower = "".join(url_stripped.lower().split())
            for scheme in _dangerous_schemes:
                if url_lower.startswith(scheme):
                    raise ValidationError(
                        _("Service URL contains a dangerous scheme "
                          "(%(scheme)s). Service: %(service)s",
                          scheme=scheme.rstrip(":"),
                          service=rec.name)
                    )
            if not _url_re.match(url_stripped):
                raise ValidationError(
                    _("'%(url)s' is not a valid URL. Service: %(service)s",
                      url=rec.url,
                      service=rec.name)
                )

    # ------------------------------------------------------------------
    # Archive support (Odoo standard)
    # ------------------------------------------------------------------
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Internal management
    # ------------------------------------------------------------------
    internal_manager_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Internal Manager",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # External sharing
    # ------------------------------------------------------------------
    share_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="woow_service_share_partner_rel",
        column1="service_id",
        column2="partner_id",
        string="Shared With",
    )

    # ------------------------------------------------------------------
    # Description / notes
    # ------------------------------------------------------------------
    description = fields.Html(string="Description")
    notes = fields.Text(string="Internal Notes")

    # ------------------------------------------------------------------
    # Portal mixin
    # ------------------------------------------------------------------
    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f"/my/services/{rec.id}"

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def get_full_url(self):
        """Return URL with scheme. Public method usable from QWeb templates."""
        self.ensure_one()
        raw = (self.url or "").strip()
        if raw and not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
        return raw

    def action_open_service(self):
        """Open the service URL in a new browser tab."""
        self.ensure_one()
        url = self.get_full_url()
        if not url:
            raise UserError(_("No URL configured for this service."))
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
