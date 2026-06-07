---
module: woow_service_hub
version: 18.0.1.0.0
odoo_version: 18.0
license: LGPL-3
author: WoowTech
website: https://woowtech.com
category: Productivity
application: true
auto_install: false
dependencies: [mail, portal, hr]
models: [woow.service, woow.service.category]
portal_routes: [/my/services, /my/services/<int:service_id>]
security_groups: [woow_service_hub_group_user, woow_service_hub_group_admin]
module_category_xml_id: woow_service_hub.module_category_woow_service_hub
---

# LLM Knowledge Base: woow_service_hub

> **Purpose**: Machine-parseable technical reference for `woow_service_hub` Odoo 18 module. Designed for LLMs to answer questions accurately. Every section is independently parseable.

---

## 1. MODULE OVERVIEW

WoowTech Service Hub centralizes internal SaaS/web services into a card catalogue within Odoo 18.

### 1.1 Capabilities

| Feature | Details |
|---------|---------|
| Kanban wall | Logo/icon/initial fallback, color tags, one-click launch |
| Permission model | Admin (CRUD), User (read-only), Portal (shared-only read) |
| Portal sharing | Share services with external contacts via `share_partner_ids` |
| Portal pages | `/my/services` (paginated grid), `/my/services/<id>` (detail) |
| Portal search | Filter by name or category name with ilike |
| Portal sort | "Name" and "Category" options via searchbar |
| Portal pagination | `portal_pager` with step=18 |
| Record pager | Prev/next navigation on detail page |
| Chatter | `mail.thread` + `mail.activity.mixin` + portal message thread |
| URL auto-complete | Auto-prepend `https://` if missing |
| Archive support | Standard Odoo `active` field |
| Category tags | Color indices for visual classification |
| Internal manager | Linked to `hr.employee` |
| i18n | zh_TW (Traditional Chinese) translations |

### 1.2 Boundaries (Anti-Features)

| Not Supported | Reason |
|---------------|--------|
| Multi-tenancy | Single-company design |
| `website` module | Uses portal standalone |
| Workflow/state machine | No transitions |
| Custom JS components | Uses standard Odoo widgets |
| REST API | Standard JSON-RPC only |
| Credential management | Out of scope |
| Service monitoring | Out of scope |

---

## 2. DATA MODEL

### 2.1 Model: `woow.service.category`

| Attribute | Value |
|-----------|-------|
| `_name` | `woow.service.category` |
| `_description` | `Service Category` |
| `_order` | `name` |
| `_inherit` | _(none)_ |

**Fields:**

| Name | Type | Required | Translate | Notes |
|------|------|----------|-----------|-------|
| `name` | `Char` | Yes | Yes | Category display name |
| `color` | `Integer` | No | No | Color index for `many2many_tags` widget |

**SQL Constraints:**

| Name | SQL | Message |
|------|-----|---------|
| `name_uniq` | `UNIQUE(name)` | `Category name must be unique!` |

---

### 2.2 Model: `woow.service`

| Attribute | Value |
|-----------|-------|
| `_name` | `woow.service` |
| `_description` | `Service` |
| `_order` | `name` |
| `_inherit` | `['mail.thread', 'mail.activity.mixin', 'portal.mixin']` |

**Fields:**

| Name | Type | Comodel | Required | Compute | Store | Tracking | Notes |
|------|------|---------|----------|---------|-------|----------|-------|
| `name` | `Char` | - | Yes | - | Yes | Yes | Service display name |
| `logo` | `Image` | - | No | - | Yes | No | max_width=256, max_height=256 |
| `icon` | `Char` | - | No | - | Yes | No | Font Awesome class, e.g. `fa-rocket` |
| `color` | `Integer` | - | No | - | Yes | No | Kanban card color index |
| `category_ids` | `Many2many` | `woow.service.category` | No | - | Yes | No | relation=`woow_service_category_rel` |
| `url` | `Char` | - | No | - | Yes | No | Raw user-entered URL |
| `full_url` | `Char` | - | No | `_compute_full_url` | **No** | No | Auto-prepends `https://` |
| `active` | `Boolean` | - | No | - | Yes | No | Default=True |
| `internal_manager_id` | `Many2one` | `hr.employee` | No | - | Yes | Yes | Internal responsible person |
| `share_partner_ids` | `Many2many` | `res.partner` | No | - | Yes | No | relation=`woow_service_share_partner_rel` |
| `description` | `Html` | - | No | - | Yes | No | Public description |
| `notes` | `Text` | - | No | - | Yes | No | Internal notes (not shown on portal) |

**Inherited fields:** `message_ids`, `message_follower_ids`, `access_url`, `access_token`, `access_warning`

**Methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `_compute_full_url` | None | Sets `full_url`. Strips whitespace, prepends `https://` if url lacks `http://` or `https://`. |
| `_compute_access_url` | None | Overrides `portal.mixin`. Sets `access_url = f"/my/services/{rec.id}"`. |
| `action_open_service` | dict | `ensure_one()`. Returns `ir.actions.act_url` with `target='new'`. Raises `UserError` if `full_url` is falsy. |

**`_compute_full_url` Truth Table:**

| Input `url` | Output `full_url` |
|-------------|-------------------|
| `None` / `""` / `False` | `""` |
| `"  "` (whitespace) | `""` |
| `"slack.com"` | `"https://slack.com"` |
| `"  example.com  "` | `"https://example.com"` |
| `"https://github.com"` | `"https://github.com"` |
| `"http://insecure.com"` | `"http://insecure.com"` |

---

## 3. SECURITY ARCHITECTURE

### 3.1 Module Category

| XML ID | Name | Sequence |
|--------|------|----------|
| `woow_service_hub.module_category_woow_service_hub` | Service Hub | 200 |

### 3.2 Security Groups

| XML ID | Name | `implied_ids` | Default Users |
|--------|------|---------------|---------------|
| `woow_service_hub.woow_service_hub_group_user` | User | `base.group_user` | _(none)_ |
| `woow_service_hub.woow_service_hub_group_admin` | Administrator | `woow_service_hub_group_user` | `base.user_root`, `base.user_admin` |

**Hierarchy:** Portal (`base.group_portal`) < User < Admin

### 3.3 ACL Matrix (`ir.model.access.csv`)

| Group | `woow.service` | `woow.service.category` |
|-------|----------------|-------------------------|
| Portal (`base.group_portal`) | R--- | ---- (no access) |
| User (`woow_service_hub_group_user`) | R--- | R--- |
| Admin (`woow_service_hub_group_admin`) | RWCD | RWCD |

**Raw CSV:**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_woow_service_user,woow.service.user,model_woow_service,woow_service_hub_group_user,1,0,0,0
access_woow_service_admin,woow.service.admin,model_woow_service,woow_service_hub_group_admin,1,1,1,1
access_woow_service_category_user,woow.service.category.user,model_woow_service_category,woow_service_hub_group_user,1,0,0,0
access_woow_service_category_admin,woow.service.category.admin,model_woow_service_category,woow_service_hub_group_admin,1,1,1,1
access_woow_service_portal,woow.service.portal,model_woow_service,base.group_portal,1,0,0,0
```

### 3.4 Record Rules

| XML ID | Model | Domain | Groups | Permissions |
|--------|-------|--------|--------|-------------|
| `woow_service_portal_rule` | `woow.service` | `[('share_partner_ids','in',[user.partner_id.id])]` | `base.group_portal` | R--- |
| `woow_service_user_rule` | `woow.service` | `[(1,'=',1)]` | `woow_service_hub_group_user` | R--- |
| `woow_service_admin_rule` | `woow.service` | `[(1,'=',1)]` | `woow_service_hub_group_admin` | RWCD |

### 3.5 Portal Access Pattern

Defense in depth (two layers):
1. **Controller** (`controllers/portal.py`): Uses `.sudo()` + manual `("share_partner_ids", "in", [partner.id])` domain filter. Redirects to `/my` if service not found or not shared.
2. **Record rule** (`woow_service_portal_rule`): ORM-level backup preventing unshared reads even via direct JSON-RPC.

---

## 4. VIEW ARCHITECTURE

### 4.1 View Registry

| XML ID | Model | Type | Key Features |
|--------|-------|------|--------------|
| `woow_service_view_kanban` | `woow.service` | kanban | `class="o_kanban_mobile"`, `highlight_color="color"`, `<t t-name="card">` with `<aside>+<main>` |
| `woow_service_view_form` | `woow.service` | form | Header button, `oe_avatar`, notebook tabs, `<chatter/>` |
| `woow_service_view_list` | `woow.service` | list | Odoo 18 `<list>` tag |
| `woow_service_view_search` | `woow.service` | search | Fields + Group By filters |
| `woow_service_category_view_list` | `woow.service.category` | list | `editable="bottom"` |
| `woow_service_category_view_form` | `woow.service.category` | form | name + color |

### 4.2 Actions

| XML ID | Model | `view_mode` | Search View |
|--------|-------|-------------|-------------|
| `woow_service_action` | `woow.service` | `kanban,list,form` | `woow_service_view_search` |
| `woow_service_category_action` | `woow.service.category` | `list,form` | _(default)_ |

### 4.3 Kanban Card Layout

```
+--------------------------------------------------+
| <aside>              | <main>                     |
|  [Logo 90x90]        |  Service Name (fs-5, bold) |
|  OR [FA Icon 90x90]  |  [Category Tags w/ colors] |
|  OR [Initial 90x90]  |  Manager (fa-user-o icon)  |
|                      |  [Open Service] btn-primary|
+--------------------------------------------------+
```

**Kanban-specific details:**
- `highlight_color="color"` on `<kanban>` element
- Category tags: `widget="many2many_tags" options="{'color_field': 'color'}"`
- Manager line: `<i class="fa fa-user-o me-1" title="Internal Manager"/>`
- Open button: `name="action_open_service" type="object" class="btn btn-primary btn-sm"`

**Logo/Icon/Initial fallback:**

| Priority | Condition | Rendering |
|----------|-----------|-----------|
| 1 | `record.logo.raw_value` truthy | `<field name="logo" widget="image">` |
| 2 | `record.icon.value` truthy | `<i class="fa #{record.icon.value}"/>` in 90x90 bg-100 box |
| 3 | Neither | First letter uppercased, white on `#00897B` |

### 4.4 Form Notebook Tabs

| Tab | Field | Visibility |
|-----|-------|------------|
| General | `description` (Html) | Public (shown on portal) |
| Sharing | `share_partner_ids` | Admin-only |
| Notes | `notes` (Text) | Internal only |

### 4.5 Search View

| Type | Name | Domain/Context |
|------|------|----------------|
| Field | name | searchable |
| Field | category_ids | searchable |
| Field | internal_manager_id | searchable |
| Field | url | searchable |
| Group By | group_category | `{'group_by': 'category_ids'}` |
| Group By | group_manager | `{'group_by': 'internal_manager_id'}` |

### 4.6 Menu Structure

```
Service Hub                                    [woow_service_hub_menu_root]
  sequence=200, web_icon=woow_service_hub,static/description/icon.png
  +-- All Services                             [woow_service_hub_menu_services]
  |   sequence=10, action=woow_service_action, groups=woow_service_hub_group_user
  +-- Categories                               [woow_service_hub_menu_categories]
      sequence=20, action=woow_service_category_action, groups=woow_service_hub_group_admin
```

---

## 5. PORTAL INTEGRATION

### 5.1 Controller

| Class | Parent | File |
|-------|--------|------|
| `WoowServicePortal` | `CustomerPortal` | `controllers/portal.py` |

**Import:**
```python
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
```

### 5.2 Routes

| Route | Method | Params | Description |
|-------|--------|--------|-------------|
| `/my/services` | `portal_my_services` | `page=1, sortby=None, search=None` | Paginated card grid |
| `/my/services/<int:service_id>` | `portal_my_service_detail` | - | Detail page with chatter |

### 5.3 Controller Features

| Feature | Implementation |
|---------|----------------|
| Pagination | `portal_pager(url="/my/services", step=18, ...)` |
| Search | Filters by `name ilike` OR `category_ids.name ilike` |
| Sorting | `_service_get_searchbar_sortings()` returns "Name" and "Category" |
| Category sort | Python-level: `sorted(key=lambda s: (s.category_ids[:1].name, s.name))` |
| Record pager | Computes `prev_record` and `next_record` URLs on detail page |
| Access control | `.sudo().search([..., ("share_partner_ids", "in", [partner.id])])` |
| Chatter auth | `service._portal_ensure_token()` |

**`_service_get_searchbar_sortings()` return value:**
```python
{
    "name": {"label": "Name", "order": "name asc"},
    "category": {"label": "Category", "order": "name asc"},
}
```

### 5.4 Portal Templates

| XML ID | Inherits | Purpose |
|--------|----------|---------|
| `portal_my_home_service` | `portal.portal_my_home` | Adds "Services" entry via `portal.portal_docs_entry` |
| `portal_my_services_breadcrumbs` | `portal.portal_breadcrumbs` | Breadcrumbs for `/my/services` |
| `portal_my_services` | _(standalone)_ | Card grid with searchbar + pager |
| `portal_my_service_detail` | `portal.portal_sidebar` (`primary="True"`) | Detail page with sidebar + chatter |

### 5.5 Portal Home Entry (`portal.portal_docs_entry` params)

```xml
<t t-set="icon" t-value="'/woow_service_hub/static/src/img/service-hub.svg'"/>
<t t-set="title">Services</t>
<t t-set="url" t-value="'/my/services'"/>
<t t-set="text">Browse services shared with you</t>
<t t-set="config_card" t-value="True"/>
```

### 5.6 Portal Detail Template Structure

Uses `portal.portal_sidebar` layout:

| Component | Usage |
|-----------|-------|
| `portal.portal_record_sidebar` | Sidebar with avatar (80x80), categories, URL, manager, Open button |
| `o_portal_content` | Main content: name, categories, description, chatter |
| `portal.portal_back_in_edit_mode` | Backend edit link (visible to User+ groups) |
| `portal.message_thread` | Portal chatter |
| Record pager | `prev_record` / `next_record` URLs from controller |

### 5.7 Avatar Sizes

| Context | Size |
|---------|------|
| Backend kanban | 90x90px |
| Portal card grid | 48x48px |
| Portal detail sidebar | 80x80px |

---

## 6. FRONTEND ASSETS

### 6.1 Asset Bundle

```python
"assets": {
    "web.assets_frontend": [
        "woow_service_hub/static/src/css/portal.css",
    ],
},
```

### 6.2 Actual CSS (5 lines)

```css
/* Safety: constrain user-uploaded images in service descriptions */
.o_portal_content img {
    max-width: 100%;
    height: auto;
}
```

### 6.3 Portal Layout Notes

- **No custom CSS classes** for portal cards (`.woow_service_card_grid`, etc. do NOT exist)
- Portal layout uses **Bootstrap utility classes** inline in QWeb templates:
  - Grid: `o_portal_docs row g-2`, `o_portal_index_card col-md-6 col-lg-4`
  - Cards: `d-flex gap-2 rounded bg-100 align-items-center`
  - Responsive: Bootstrap grid handles breakpoints

---

## 7. GOTCHAS AND ANTI-PATTERNS

| Issue | Details |
|-------|---------|
| `full_url` is `store=False` | Do NOT query it in SQL or search domains. Use `url` field for searches. |
| `portal.css` only constrains images | All portal layout is Bootstrap utilities in QWeb, not custom CSS. |
| Import order | `woow_service_category` must import before `woow_service` (comodel dependency). |
| `share_partner_ids` is `res.partner` | NOT `res.users`. Portal access is partner-based. |
| Record rules + `.sudo()` | Both layers required. Do not remove either. |
| Category sort is Python-level | M2M fields cannot be SQL-sorted. |

---

## 8. SECURITY ASSERTIONS

Use these for testing/verification:

| Assertion | Expected |
|-----------|----------|
| Portal user reads `woow.service.category` | MUST fail (no ACL entry) |
| Portal user reads service not in `share_partner_ids` | MUST fail (record rule) |
| User group creates `woow.service` | MUST fail (ACL: perm_create=0) |
| User group creates `woow.service.category` | MUST fail (ACL: perm_create=0) |
| Admin group full CRUD on both models | MUST succeed |
| `action_open_service()` with falsy `full_url` | MUST raise `UserError` |
| Portal user hits `/my/services/<id>` for unshared service | MUST redirect to `/my` (controller returns `request.redirect("/my")`) |
| Portal user hits `/my/services/<id>` for non-existent ID | MUST redirect to `/my` (same path — search returns empty) |

---

## 9. EXTENSION DECISION TREES

### 9.1 How to Add a New Field

**Affected files:**
1. `models/woow_service.py` or `models/woow_service_category.py`
2. `views/woow_service_views.xml` (if backend visible)
3. `views/portal_templates.xml` (if portal visible)
4. `i18n/*.po` (if translatable)

**Template:**
```python
# In models/woow_service.py
new_field = fields.Char(string="New Field", help="Description")
```

```xml
<!-- In views/woow_service_views.xml (form view) -->
<field name="new_field"/>
```

### 9.2 How to Add a New Portal Route

**Affected files:**
1. `controllers/portal.py`
2. `views/portal_templates.xml`

**Controller pattern:**
```python
@http.route("/my/services/custom", type="http", auth="user", website=True)
def portal_custom(self, **kwargs):
    partner = request.env.user.partner_id
    # Use .sudo() + manual domain filter
    data = request.env["woow.service"].sudo().search([
        ("share_partner_ids", "in", [partner.id]),
        # additional filters
    ])
    return request.render("woow_service_hub.portal_custom", {"data": data})
```

**Template pattern:**
```xml
<template id="portal_custom" name="Custom Page">
    <t t-call="portal.portal_layout">
        <!-- content -->
    </t>
</template>
```

### 9.3 How to Add a New Security Group

**Affected files:**
1. `security/woow_service_hub_groups.xml`
2. `security/ir.model.access.csv`
3. `security/woow_service_hub_rules.xml` (if record-level rules needed)

**Groups XML:**
```xml
<record id="woow_service_hub_group_manager" model="res.groups">
    <field name="name">Manager</field>
    <field name="category_id" ref="module_category_woow_service_hub"/>
    <field name="implied_ids" eval="[(4, ref('woow_service_hub_group_user'))]"/>
</record>
```

**ACL CSV:**
```csv
access_woow_service_manager,woow.service.manager,model_woow_service,woow_service_hub_group_manager,1,1,0,0
```

### 9.4 How to Add Searchbar Sorting Option

**Affected file:** `controllers/portal.py`

**Pattern:**
```python
def _service_get_searchbar_sortings(self):
    return {
        "name": {"label": "Name", "order": "name asc"},
        "category": {"label": "Category", "order": "name asc"},
        "new_sort": {"label": "New Sort", "order": "field_name desc"},
    }
```

For M2M or computed fields, use Python-level sort:
```python
if sortby == "new_sort":
    services = services.sorted(key=lambda s: s.computed_value or "")
```

### 9.5 How to Change Permissions for an Existing Group

**Affected files:**
1. `security/ir.model.access.csv` (ACL changes)
2. `security/woow_service_hub_rules.xml` (record rule changes)

**Example: Upgrade User group from R--- to RW-- on `woow.service`:**

1. In `ir.model.access.csv`, change the User line:
```csv
# Before:
access_woow_service_user,woow.service.user,model_woow_service,woow_service_hub_group_user,1,0,0,0
# After (add write):
access_woow_service_user,woow.service.user,model_woow_service,woow_service_hub_group_user,1,1,0,0
```

2. In `woow_service_hub_rules.xml`, update the User record rule:
```xml
<!-- Before: R only -->
<field name="perm_write" eval="False"/>
<!-- After: R + W -->
<field name="perm_write" eval="True"/>
```

3. Upgrade module: `odoo -d <database> -u woow_service_hub --stop-after-init`

**Checklist:**
- ACL (`ir.model.access.csv`) controls model-level access
- Record rules (`woow_service_hub_rules.xml`) control record-level access + domain
- Both must agree — ACL denies overrides record rule allows

---

## 10. DEMO DATA CATALOG

### 10.1 Categories (10)

| XML ID | Name | Color |
|--------|------|-------|
| `category_communication` | Communication | 1 |
| `category_project_mgmt` | Project Management | 2 |
| `category_design` | Design | 3 |
| `category_dev_tools` | DevOps / Dev Tools | 4 |
| `category_cloud` | Cloud / Infra | 5 |
| `category_analytics` | Analytics | 6 |
| `category_storage` | Storage / Docs | 7 |
| `category_finance` | Finance | 8 |
| `category_security` | Security | 9 |
| `category_hr` | HR / People | 10 |

### 10.2 Services (18)

| # | XML ID | Name | Icon | URL | Special |
|---|--------|------|------|-----|---------|
| 1 | `service_slack` | Slack | `fa-slack` | `woowtech.slack.com` | - |
| 2 | `service_github` | GitHub | `fa-github` | `github.com/woowtech` | - |
| 3 | `service_figma` | Figma | `fa-paint-brush` | `figma.com` | - |
| 4 | `service_jira` | Jira | `fa-tasks` | `woowtech.atlassian.net` | - |
| 5 | `service_google_workspace` | Google Workspace | `fa-google` | `workspace.google.com` | - |
| 6 | `service_aws` | AWS Console | `fa-cloud` | `console.aws.amazon.com` | - |
| 7 | `service_grafana` | Grafana | `fa-line-chart` | `grafana.woowtech.com` | - |
| 8 | `service_notion` | Notion | `fa-file-text-o` | `notion.so` | - |
| 9 | `service_1password` | 1Password | `fa-lock` | `woowtech.1password.com` | - |
| 10 | `service_linear` | Linear | `fa-bolt` | `linear.app` | - |
| 11 | `service_sentry` | Sentry | `fa-bug` | `woowtech.sentry.io` | - |
| 12 | `service_hackmd` | HackMD | `fa-pencil-square-o` | `hackmd.io` | - |
| 13 | `service_odoo` | Odoo ERP | `fa-building` | `localhost:9103` | - |
| 14 | `service_trello` | Trello | `fa-trello` | `trello.com` | Retired |
| 15 | `service_heroku` | Heroku | `fa-server` | `dashboard.heroku.com` | Retired |
| 16 | `service_n8n` | n8n Automation | _(none)_ | `n8n.woowtech.com` | Tests initial fallback |
| 17 | `service_miro` | Miro | _(none)_ | `miro.com` | Tests initial fallback |
| 18 | `service_tailscale` | Tailscale | `fa-shield` | _(none)_ | Tests `UserError` |

---

## 11. I18N

### 11.1 Translation Files

| File | Locale | Status |
|------|--------|--------|
| `i18n/woow_service_hub.pot` | _(template)_ | Complete |
| `i18n/zh_TW.po` | zh_TW | Complete |

### 11.2 Key Translations

| English | zh_TW |
|---------|-------|
| Service Hub | 服務中心 |
| All Services | 所有服務 |
| Categories | 分類 |
| Service Name | 服務名稱 |
| Open Service | 開啟服務 |
| No URL configured for this service. | 此服務未設定網址。 |
| Category name must be unique! | 分類名稱不可重複！ |

---

## 12. CODE ARCHITECTURE

### 12.1 File Structure

```
woow_service_hub/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── portal.py
├── demo/
│   └── demo_data.xml
├── i18n/
│   ├── woow_service_hub.pot
│   └── zh_TW.po
├── models/
│   ├── __init__.py
│   ├── woow_service_category.py
│   └── woow_service.py
├── security/
│   ├── woow_service_hub_groups.xml
│   ├── ir.model.access.csv
│   └── woow_service_hub_rules.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── css/
│       │   └── portal.css
│       └── img/
│           └── service-hub.svg
└── views/
    ├── portal_templates.xml
    ├── woow_service_category_views.xml
    ├── woow_service_hub_menus.xml
    └── woow_service_views.xml
```

### 12.2 Import Order

```python
# models/__init__.py
from . import woow_service_category  # MUST be first (comodel)
from . import woow_service
```

### 12.3 XML Loading Order

```python
"data": [
    # 1. security (groups before ACL before rules)
    "security/woow_service_hub_groups.xml",
    "security/ir.model.access.csv",
    "security/woow_service_hub_rules.xml",
    # 2. views (views before menus)
    "views/woow_service_category_views.xml",
    "views/woow_service_views.xml",
    "views/woow_service_hub_menus.xml",
    # 3. portal (last, inherits external templates)
    "views/portal_templates.xml",
],
```

---

## 13. ODOO 18 COMPATIBILITY

| Feature | Odoo 18 Syntax |
|---------|----------------|
| List view | `<list>` (not `<tree>`) |
| Kanban card | `<t t-name="card">` with `<aside>+<main>` |
| Chatter | `<chatter/>` |
| Kanban highlight | `highlight_color="color"` attribute |
| Portal counter | `_prepare_home_portal_values(counters)` |

---

## 14. XML ID QUICK REFERENCE

### Security

- `woow_service_hub.module_category_woow_service_hub`
- `woow_service_hub.woow_service_hub_group_user`
- `woow_service_hub.woow_service_hub_group_admin`
- `woow_service_hub.woow_service_portal_rule`
- `woow_service_hub.woow_service_user_rule`
- `woow_service_hub.woow_service_admin_rule`

### Views

- `woow_service_hub.woow_service_view_kanban`
- `woow_service_hub.woow_service_view_form`
- `woow_service_hub.woow_service_view_list`
- `woow_service_hub.woow_service_view_search`
- `woow_service_hub.woow_service_category_view_list`
- `woow_service_hub.woow_service_category_view_form`

### Actions

- `woow_service_hub.woow_service_action`
- `woow_service_hub.woow_service_category_action`

### Menus

- `woow_service_hub.woow_service_hub_menu_root`
- `woow_service_hub.woow_service_hub_menu_services`
- `woow_service_hub.woow_service_hub_menu_categories`

### Portal Templates

- `woow_service_hub.portal_my_home_service`
- `woow_service_hub.portal_my_services_breadcrumbs`
- `woow_service_hub.portal_my_services`
- `woow_service_hub.portal_my_service_detail`

---

## 15. DATABASE TABLES

| Model | Table |
|-------|-------|
| `woow.service` | `woow_service` |
| `woow.service.category` | `woow_service_category` |
| M2M: service-category | `woow_service_category_rel` |
| M2M: service-partner | `woow_service_share_partner_rel` |

---

## 16. KEY PYTHON IMPORTS

```python
# Model file
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Controller file
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
```
