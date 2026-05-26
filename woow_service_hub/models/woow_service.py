from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
