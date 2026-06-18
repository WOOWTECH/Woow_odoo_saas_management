# Task Plan: woow_service_hub Odoo 18 Module

## Goal
Build a complete Odoo 18 module `woow_service_hub` — WoowTech's internal service portal with colourful card catalogue, three-tier access control, chatter discussions, and portal sharing for external contacts.

## Current Phase
All phases complete — ready for deployment testing.

## Phases

### Phase 1: Module Skeleton ✓
- [x] Directory structure + `__init__.py` files
- [x] `__manifest__.py` (depends: mail, portal, hr)
- [x] `woow.service.category` model (name + color)
- [x] `woow.service` model (all fields + action_open_service)
- [x] Design decisions confirmed via brainstorming Q&A
- **Status:** complete

### Phase 2: Security — Groups, ACL, Record Rules ✓
- [x] Create `module_category` XML for "Service Hub" in Settings → Users
- [x] Define 2 groups: `woow_service_hub_user` (User) + `woow_service_hub_admin` (Admin, implies User)
- [x] Create `ir.model.access.csv` for both models × both groups + portal
- [x] Create record rule: portal users can only read services where they are in `share_partner_ids`
- [x] Record rule: internal users (User group) can read all `woow.service`
- [x] Record rule: Admin group has full CRUD
- **Status:** complete

### Phase 3: Views — Kanban, Form, List, Search, Menus ✓
- [x] `woow_service_category_views.xml`: List + Form for category management
- [x] `woow_service_views.xml` — Kanban view with Odoo 18 syntax, aside/main, colour tags, badge, open button
- [x] Form view with statusbar, logo, notebook (General/Sharing/Notes), chatter
- [x] List view with key columns
- [x] Search view with state filters, default exclude-retired, Group By options
- [x] Menu structure: flat 2-level (All Services + Categories admin-only)
- **Status:** complete

### Phase 4: Interactions — Chatter, One-Click Launch, Colour Tags ✓
- [x] `action_open_service()` raises `UserError` when URL is empty
- [x] mail.thread / mail.activity.mixin integrated via `<chatter/>` in form
- [x] many2many_tags with `color_field` in Kanban + Form
- [x] `highlight_color="color"` on kanban element for card colouring
- **Status:** complete

### Phase 5: Portal — Controller, Templates, /my/services ✓
- [x] Portal controller inheriting `CustomerPortal` with sidebar count
- [x] Route `/my/services` → card grid (no paging)
- [x] Route `/my/services/<int:service_id>` → detail page + open button
- [x] Portal templates with logo/icon/initial fallback, state badge, open button
- [x] `_compute_access_url()` override for portal.mixin
- [x] Custom CSS for card grid layout (`portal.css`)
- [x] Record rule for portal users (share_partner_ids)
- **Status:** complete

### Phase 6: Manifest Finalization ✓
- [x] All data file entries active in `__manifest__.py`
- [x] Assets section for `web.assets_frontend` (portal CSS)
- [x] Module icon (`static/description/icon.png`)
- **Status:** complete

### Code Review Fixes ✓
- [x] C1: Added `icon.png` for app drawer and portal sidebar
- [x] C2: Removed unused `import base64` from controller
- [x] C3/C4: Verified portal XPath, `placeholder_count`, `_prepare_home_portal_values(counters)` signature — all correct for Odoo 18
- [x] I4: Changed `color_picker` to `color` widget for integer color index fields
- [x] I5: Added `highlight_color="color"` to `<kanban>` element
- [x] S1: Added `_sql_constraints` unique name on `woow.service.category`
- **Status:** complete

## Key Questions (All Answered)
1. State labels → English + .po i18n
2. Fallback → name initial letter (Gmail-style)
3. Kanban ordering → by name, Group By in search
4. Portal fields → name + logo/icon + state + description + open button
5. Empty URL → UserError
6. Retired → hidden by default filter
7. Category management → dedicated admin-only submenu
8. Menu → flat 2-level
9. Portal layout → card grid
10. Pagination → none
11. Groups → own module_category
12. Display name → default name

## Files Created
```
woow_service_hub/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── portal.py
├── models/
│   ├── __init__.py
│   ├── woow_service.py
│   └── woow_service_category.py
├── security/
│   ├── ir.model.access.csv
│   ├── woow_service_hub_groups.xml
│   └── woow_service_hub_rules.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       └── css/
│           └── portal.css
└── views/
    ├── portal_templates.xml
    ├── woow_service_category_views.xml
    ├── woow_service_hub_menus.xml
    └── woow_service_views.xml
```

## Notes
- Odoo 18 view syntax: `<list>` not `<tree>`, Kanban uses `<t t-name="card">`
- portal module does NOT depend on website
- User's Odoo user_id=9, employee_id=7
- Environment: localhost:9103, DB: odoo-saasmanage, admin/admin
