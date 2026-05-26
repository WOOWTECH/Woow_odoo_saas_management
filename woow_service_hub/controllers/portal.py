from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class WoowServicePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "service_count" in counters:
            partner = request.env.user.partner_id
            values["service_count"] = (
                request.env["woow.service"]
                .sudo()
                .search_count([("share_partner_ids", "in", [partner.id])])
            )
        return values

    @http.route(
        "/my/services",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_services(self, **kwargs):
        partner = request.env.user.partner_id
        services = (
            request.env["woow.service"]
            .sudo()
            .search([("share_partner_ids", "in", [partner.id])])
        )
        values = self._prepare_portal_layout_values()
        values.update({
            "services": services,
            "page_name": "services",
        })
        return request.render(
            "woow_service_hub.portal_my_services", values
        )

    @http.route(
        "/my/services/<int:service_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_service_detail(self, service_id, **kwargs):
        partner = request.env.user.partner_id
        service = (
            request.env["woow.service"]
            .sudo()
            .search([
                ("id", "=", service_id),
                ("share_partner_ids", "in", [partner.id]),
            ], limit=1)
        )
        if not service:
            return request.redirect("/my")
        # Ensure access token exists for portal chatter
        service._portal_ensure_token()
        values = self._prepare_portal_layout_values()
        values.update({
            "service": service,
            "page_name": "service_detail",
            # Portal chatter context
            "token": service.access_token,
            "pid": partner.id,
            "hash": "",
        })
        return request.render(
            "woow_service_hub.portal_my_service_detail", values
        )
