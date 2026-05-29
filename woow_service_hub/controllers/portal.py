from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


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

    def _service_get_searchbar_sortings(self):
        return {
            "name": {"label": "Name", "order": "name asc"},
            "category": {"label": "Category", "order": "category_ids asc, name asc"},
        }

    @http.route(
        "/my/services",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_services(self, page=1, sortby=None, search=None, **kwargs):
        partner = request.env.user.partner_id
        ServiceSudo = request.env["woow.service"].sudo()
        domain = [("share_partner_ids", "in", [partner.id])]

        # Searchbar sortings
        searchbar_sortings = self._service_get_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        # Search filter
        if search:
            domain = [
                ("share_partner_ids", "in", [partner.id]),
                "|",
                ("name", "ilike", search),
                ("category_ids.name", "ilike", search),
            ]

        # Count & pager
        service_count = ServiceSudo.search_count(domain)
        pager = portal_pager(
            url="/my/services",
            url_args={"sortby": sortby, "search": search or ""},
            total=service_count,
            page=page,
            step=18,
        )

        services = ServiceSudo.search(
            domain, order=order, limit=18, offset=pager["offset"]
        )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "services": services,
                "page_name": "services",
                "pager": pager,
                "default_url": "/my/services",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "search_in": "all",
                "search": search or "",
            }
        )
        return request.render("woow_service_hub.portal_my_services", values)

    @http.route(
        "/my/services/<int:service_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_service_detail(self, service_id, **kwargs):
        partner = request.env.user.partner_id
        ServiceSudo = request.env["woow.service"].sudo()

        service = ServiceSudo.search(
            [
                ("id", "=", service_id),
                ("share_partner_ids", "in", [partner.id]),
            ],
            limit=1,
        )
        if not service:
            return request.redirect("/my")

        # Ensure access token exists for portal chatter
        service._portal_ensure_token()

        # Record pager (prev/next)
        all_services = ServiceSudo.search(
            [("share_partner_ids", "in", [partner.id])], order="name asc"
        )
        service_ids = all_services.ids
        current_idx = service_ids.index(service.id) if service.id in service_ids else 0
        prev_record = (
            "/my/services/%s" % service_ids[current_idx - 1]
            if current_idx > 0
            else None
        )
        next_record = (
            "/my/services/%s" % service_ids[current_idx + 1]
            if current_idx < len(service_ids) - 1
            else None
        )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "service": service,
                "page_name": "service_detail",
                # Portal chatter context
                "token": service.access_token,
                "pid": partner.id,
                "hash": "",
                # Record pager
                "prev_record": prev_record,
                "next_record": next_record,
            }
        )
        return request.render("woow_service_hub.portal_my_service_detail", values)
