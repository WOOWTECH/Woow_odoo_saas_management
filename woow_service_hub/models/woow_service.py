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
    icon = fields.Char(
        string="Font Awesome Icon",
        help="Font Awesome class, e.g. 'fa-rocket'. Used as fallback when no logo is set.",
    )
    color = fields.Integer(string="Card Color")

    # ------------------------------------------------------------------
    # WELL Building Standard category
    # ------------------------------------------------------------------
    well_category = fields.Selection([
        ('health', 'Health & Wellness Program'),
        ('eap', 'EAP Mental Health Support'),
        ('fitness', 'Fitness & Movement'),
        ('nutrition', 'Nutrition & Nourishment'),
        ('environment', 'Environmental Monitoring'),
        ('none', 'General Service'),
    ], string='WELL Category', default='none',
        help='WELL Building Standard service category classification')

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
    full_url = fields.Char(
        string="Full URL",
        compute="_compute_full_url",
        store=False,
    )

    @api.depends("url")
    def _compute_full_url(self):
        for rec in self:
            raw = (rec.url or "").strip()
            if raw and not raw.startswith(("http://", "https://")):
                raw = "https://" + raw
            rec.full_url = raw

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("url")
    def _check_url_format(self):
        """Validate that the url field contains a well-formed URL.

        Accepts http://, https://, or bare hostnames (which get
        https:// prepended by _compute_full_url). Blocks dangerous
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
    def action_open_service(self):
        """Open the service URL in a new browser tab."""
        self.ensure_one()
        if not self.full_url:
            raise UserError(_("No URL configured for this service."))
        return {
            "type": "ir.actions.act_url",
            "url": self.full_url,
            "target": "new",
        }
