import re
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_URL_RE = re.compile(
    r"^(https?://)?"           # optional scheme
    r"[a-zA-Z0-9]"            # must start with alnum
    r"[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$",  # rest of URL
    re.IGNORECASE,
)
# "<scheme>:<rest>" (RFC 3986 scheme syntax)
_URL_SCHEME_RE = re.compile(r"^([a-z][a-z0-9+.\-]*):(.*)$", re.DOTALL)
# "<host>:<port>[/?#...]" -- a bare host with a port, not a scheme
_URL_PORT_RE = re.compile(r"^[0-9]+(?:[/?#].*)?$", re.DOTALL)
_URL_IGNORED_CHARS_RE = re.compile(r"[\x00-\x20\x7f]+")
_ALLOWED_URL_SCHEMES = ("http", "https")
# Always rejected, even in a "name:digits" shape (javascript:1/alert(1)).
_DANGEROUS_URL_SCHEMES = ("javascript:", "data:", "vbscript:")


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
        """Validate that the url field contains a well-formed http(s) URL.

        Accepts ``http://`` / ``https://`` URLs and bare hostnames
        (optionally with a port, e.g. ``localhost:9103``), which get
        ``https://`` prepended by get_full_url(). Any other explicit
        scheme (``javascript:``, ``data:``, ``ftp:``, ``mailto:``,
        ``file:`` ...) is rejected: only http and https are allowed.
        Runs on both create and write.
        """
        for rec in self:
            if not rec.url:
                continue
            url_stripped = rec.url.strip()
            # Browsers ignore embedded whitespace / control characters
            # inside a scheme ("java\tscript:"), so compare on a
            # compacted copy.
            url_compact = _URL_IGNORED_CHARS_RE.sub("", url_stripped).lower()
            for scheme in _DANGEROUS_URL_SCHEMES:
                if url_compact.startswith(scheme):
                    raise ValidationError(
                        _("Service URL contains a dangerous scheme "
                          "(%(scheme)s). Service: %(service)s",
                          scheme=scheme.rstrip(":"),
                          service=rec.name)
                    )
            scheme_match = _URL_SCHEME_RE.match(url_compact)
            if scheme_match:
                scheme, rest = scheme_match.groups()
                if scheme in _ALLOWED_URL_SCHEMES:
                    if not rest.startswith("//"):
                        raise ValidationError(
                            _("'%(url)s' is not a valid URL. Service: %(service)s",
                              url=rec.url,
                              service=rec.name)
                        )
                elif not _URL_PORT_RE.match(rest):
                    # Not "host:port" -> an explicit non-http(s) scheme.
                    raise ValidationError(
                        _("Service URL must use http:// or https:// "
                          "(got %(scheme)s:). Service: %(service)s",
                          scheme=scheme,
                          service=rec.name)
                    )
            if not _URL_RE.match(url_stripped):
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
    # Internal only: portal users may read shared woow.service records
    # (ACL + "shared services only" rule) but must never see the notes.
    notes = fields.Text(
        string="Internal Notes",
        groups="woow_service_hub.woow_service_hub_group_user",
    )

    # ------------------------------------------------------------------
    # Portal mixin
    # ------------------------------------------------------------------
    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f"/my/services/{rec.id}"

    # ------------------------------------------------------------------
    # Sharing: revoke portal tokens when a partner is un-shared
    # ------------------------------------------------------------------
    def write(self, vals):
        if "share_partner_ids" not in vals:
            return super().write(vals)
        # active_test=False: an archived partner being removed still counts
        before = {
            rec.id: set(rec.with_context(active_test=False).share_partner_ids.ids)
            for rec in self
        }
        res = super().write(vals)
        revoked = self.filtered(
            lambda rec: before.get(rec.id, set())
            - set(rec.with_context(active_test=False).share_partner_ids.ids)
        )
        revoked._portal_rotate_access_token()
        return res

    def _portal_rotate_access_token(self):
        """Replace the access token so links / chatter tokens handed out to
        partners that are no longer shared stop working (the hash/pid
        signature is derived from the token as well)."""
        for rec in self:
            rec.sudo().write({"access_token": str(uuid.uuid4())})

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def get_full_url(self):
        """Return URL with scheme. Public method usable from QWeb templates."""
        self.ensure_one()
        raw = (self.url or "").strip()
        if raw and not raw.lower().startswith(("http://", "https://")):
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
