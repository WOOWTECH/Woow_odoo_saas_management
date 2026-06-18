{
    "name": "WoowTech Service Hub",
    "version": "18.0.1.0.0",
    "category": "Productivity",
    "summary": "Internal service portal — browse, launch, and share SaaS/web services",
    "description": """
WoowTech Service Hub
====================
Centralise all internal SaaS and web services into a colourful card catalogue.

* Kanban card wall with logos, colour tags and one-click launch
* Three-tier access control (Admin / User / Portal)
* Share selected services with external portal contacts
* Built-in chatter for per-service discussions
    """,
    "author": "WoowTech",
    "website": "https://woowtech.com",
    "license": "LGPL-3",
    "depends": [
        "mail",
        "portal",
        "hr",
    ],
    "data": [
        # security — groups must load before ACL and rules
        "security/woow_service_hub_groups.xml",
        "security/ir.model.access.csv",
        "security/woow_service_hub_rules.xml",
        # views
        "views/woow_service_category_views.xml",
        "views/woow_service_views.xml",
        "views/woow_service_hub_menus.xml",
        # portal
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "woow_service_hub/static/src/css/portal.css",
        ],
    },
    "demo": [
        "demo/demo_data.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
