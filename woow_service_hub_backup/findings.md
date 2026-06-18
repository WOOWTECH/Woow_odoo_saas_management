# Findings & Decisions

## Requirements
- Odoo 18 module: `woow_service_hub` (LGPL-3, prefix `woow_`)
- Internal service portal — colourful card catalogue for SaaS/web services
- One-click launch (open URL in new tab)
- Each service has: internal manager (hr.employee), colour tags, chatter
- Share specific services with external portal contacts
- Three-tier access: Admin (full CRUD), User (read-only + chatter), Hidden
- Portal: /my/services for external users to see shared services
- No multi-tenancy, no website dependency
- depends: mail, portal, hr

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| `woow.service` inherits mail.thread, mail.activity.mixin, portal.mixin | Chatter + activities + portal access |
| `woow.service.category` is standalone model | Simple tag library, colour index for widget |
| Explicit many2many relation tables | Avoids auto-naming collisions |
| `full_url` is computed, not stored | Always fresh, no sync issues |
| `fields.Image` with max 256x256 | Standard Odoo image field, auto-resize |
| `state` as Selection (not workflow) | Simple status tracking, no complex transitions needed |
| English labels + .po i18n | Standard Odoo practice, future multilang |
| Name-initial fallback in Kanban | When no logo and no FA icon, show first letter of name |
| Default filter excludes retired | Retired services hidden from daily view |
| Portal card grid (not table) | Visual consistency with service hub concept |
| No portal pagination | <20 shared services expected per partner |
| Own module_category for groups | application=True warrants own Settings section |

## Odoo 18 Specifics
- Kanban view: use `<t t-name="card">` with `<aside>` and `<main>` sections
- List view: use `<list>` tag (not `<tree>`)
- portal.mixin provides `access_url` computed field — override `_compute_access_url()`
- CustomerPortal: inherit and add `_prepare_home_portal_values()` for sidebar count
- No website module installed — portal uses basic frontend layout (expected)

## Model Field Summary

### woow.service.category
| Field | Type | Notes |
|-------|------|-------|
| name | Char | required, translate=True |
| color | Integer | colour index for tag widget |

### woow.service
| Field | Type | Notes |
|-------|------|-------|
| name | Char | required, tracking=True |
| logo | Image | max 256x256 |
| icon | Char | FA class e.g. fa-rocket |
| color | Integer | card colour |
| category_ids | M2M → woow.service.category | colour tags |
| url | Char | user-entered URL |
| full_url | Char (computed) | auto-prepend https:// |
| state | Selection | active/trial/planned/retired, default=active |
| internal_manager_id | M2O → hr.employee | tracked |
| share_partner_ids | M2M → res.partner | portal sharing |
| description | Html | public description |
| notes | Text | internal notes |

## Security Architecture

### Groups
- `module_category`: woow_service_hub (own category in Settings)
- `woow_service_hub_user`: Read access to both models
- `woow_service_hub_admin`: Full CRUD, implies user group

### ir.model.access.csv
| Group | woow.service | woow.service.category |
|-------|-------------|----------------------|
| User | R | R |
| Admin | CRUD | CRUD |

### Record Rules
- Internal User group: read all woow.service records
- Portal user: read only where `partner_id in share_partner_ids`
- Admin: full access (no domain restriction)

## Menu Structure
```
服務入口平台 (Service Hub)  ← top-level app menu
├── 所有服務 (All Services) ← Kanban + List, all internal users
└── 標籤管理 (Categories)   ← List + Form, admin-only
```

## Portal Routes
| Route | Purpose | Auth |
|-------|---------|------|
| /my/services | Card grid of shared services | portal user |
| /my/services/<id> | Service detail + open button | portal user |

## Resources
- Odoo environment: http://localhost:9103 (admin/admin, DB: odoo-saasmanage)
- Module path: woow_service_hub/ in current repo

---
*Update this file after every 2 view/browser/search operations*
