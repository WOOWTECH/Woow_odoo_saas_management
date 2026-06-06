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
translatable_locales: [en, zh_TW]
demo_categories: 10
demo_services: 18
test_suites: 2
---

# LLM Knowledge Base: woow_service_hub

> **Purpose**: Machine-parseable technical reference for the `woow_service_hub` Odoo 18 module. Designed for LLMs (Claude, GPT, etc.) to answer questions about this module accurately. Every section is independently parseable.

---

## 1. MODULE OVERVIEW

WoowTech Service Hub (WoowTech 服務中心) centralizes all internal SaaS and web services into a colorful card catalogue within Odoo 18. It provides a Kanban card wall with logos, color tags, and one-click launch; a three-tier access control system (Admin / User / Portal); sharing of selected services with external portal contacts; and built-in chatter for per-service discussions.

### Key Capabilities

- Kanban card wall with logo/icon/initial fallback, color tags, one-click launch
- Three-tier permission model: Admin (full CRUD), User (read-only), Portal (shared-only read)
- Share specific services with external portal contacts via `share_partner_ids`
- Portal pages at `/my/services` and `/my/services/<id>` with card grid layout
- Built-in chatter (mail.thread + mail.activity.mixin) for per-service discussions
- Portal chatter with access token authentication
- URL auto-completion (auto-prepend `https://` if missing)
- Archive/unarchive support via standard Odoo `active` field
- Category tags with color indices for visual classification
- Internal manager assignment (linked to `hr.employee`)
- i18n support with zh_TW (Traditional Chinese) translations

### Anti-Features / Boundaries

- No multi-tenancy support
- No `website` module dependency (uses portal standalone)
- No portal pagination (designed for <20 shared services per partner)
- No workflow/state machine transitions
- No custom JavaScript components
- No REST API endpoints (uses standard Odoo JSON-RPC only)
- Does not manage service credentials or SSO
- Does not provide service monitoring or health checks

---

## 2. DATA MODEL

### 2.1 Model: `woow.service.category`

| Attribute | Value |
|-----------|-------|
| `_name` | `woow.service.category` |
| `_description` | `Service Category` (服務分類) |
| `_order` | `name` |
| `_inherit` | _(none)_ |

#### Fields

| Name | Type | Required | Default | Translate | Tracking | Notes |
|------|------|----------|---------|-----------|----------|-------|
| `name` | `Char` | Yes | - | Yes | No | Category display name |
| `color` | `Integer` | No | - | No | No | Color index for `many2many_tags` widget |

#### SQL Constraints

| Constraint Name | SQL | Message |
|-----------------|-----|---------|
| `name_uniq` | `UNIQUE(name)` | `Category name must be unique!` (分類名稱不可重複！) |

#### Methods

_No custom methods. Standard ORM only._

---

### 2.2 Model: `woow.service`

| Attribute | Value |
|-----------|-------|
| `_name` | `woow.service` |
| `_description` | `Service` (服務) |
| `_order` | `name` |
| `_inherit` | `['mail.thread', 'mail.activity.mixin', 'portal.mixin']` |

#### Fields

| Name | Type | `comodel_name` | Required | Default | Compute | Store | Tracking | Notes |
|------|------|----------------|----------|---------|---------|-------|----------|-------|
| `name` | `Char` | - | Yes | - | - | Yes | Yes | Service display name (服務名稱) |
| `logo` | `Image` | - | No | - | - | Yes | No | max_width=256, max_height=256 |
| `icon` | `Char` | - | No | - | - | Yes | No | Font Awesome class, e.g. `fa-rocket` (圖示) |
| `color` | `Integer` | - | No | - | - | Yes | No | Kanban card color index (卡片顏色) |
| `category_ids` | `Many2many` | `woow.service.category` | No | - | - | Yes | No | relation=`woow_service_category_rel`, column1=`service_id`, column2=`category_id` |
| `url` | `Char` | - | No | - | - | Yes | No | Raw user-entered URL (服務網址) |
| `full_url` | `Char` | - | No | - | `_compute_full_url` | No | No | Computed: auto-prepends `https://` (完整網址) |
| `active` | `Boolean` | - | No | `True` | - | Yes | No | Standard Odoo archive support |
| `internal_manager_id` | `Many2one` | `hr.employee` | No | - | - | Yes | Yes | Internal responsible person (內部負責人) |
| `share_partner_ids` | `Many2many` | `res.partner` | No | - | - | Yes | No | relation=`woow_service_share_partner_rel`, column1=`service_id`, column2=`partner_id` (共享對象) |
| `description` | `Html` | - | No | - | - | Yes | No | Public description (描述) |
| `notes` | `Text` | - | No | - | - | Yes | No | Internal notes, not shown on portal (內部備註) |

_Inherited fields from `mail.thread`: `message_ids`, `message_follower_ids`, `message_partner_ids`, `message_needaction`, etc._
_Inherited fields from `portal.mixin`: `access_url`, `access_token`, `access_warning`._

#### SQL Constraints

_None on `woow.service`._

#### Methods

| Method | Signature | Return Type | Description |
|--------|-----------|-------------|-------------|
| `_compute_full_url` | `self` | `None` | Sets `full_url`. Strips whitespace from `url`, prepends `https://` if url does not start with `http://` or `https://`. Empty url produces empty `full_url`. |
| `_compute_access_url` | `self` | `None` | Overrides `portal.mixin`. Sets `access_url = f"/my/services/{rec.id}"` for each record. |
| `action_open_service` | `self` | `dict` | `ensure_one()`. Returns `ir.actions.act_url` with `url=self.full_url, target='new'`. Raises `UserError` if `full_url` is falsy. |

#### `_compute_full_url` Logic (detailed)

```python
@api.depends("url")
def _compute_full_url(self):
    for rec in self:
        raw = (rec.url or "").strip()
        if raw and not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
        rec.full_url = raw
```

**Truth table:**

| Input `url` | Output `full_url` |
|-------------|-------------------|
| `None` / `""` / `False` | `""` (empty string) |
| `"  "` (whitespace only) | `""` (empty string) |
| `"slack.com"` | `"https://slack.com"` |
| `"  example.com  "` | `"https://example.com"` |
| `"https://github.com"` | `"https://github.com"` |
| `"http://insecure.com"` | `"http://insecure.com"` |

---

## 3. SECURITY ARCHITECTURE

### 3.1 Module Category

| XML ID | Name | Sequence |
|--------|------|----------|
| `woow_service_hub.module_category_woow_service_hub` | Service Hub (服務中心) | 200 |

### 3.2 Security Groups

| XML ID | Name | `implied_ids` | Default Users |
|--------|------|---------------|---------------|
| `woow_service_hub.woow_service_hub_group_user` | User (使用者) | `base.group_user` | _(none)_ |
| `woow_service_hub.woow_service_hub_group_admin` | Administrator (管理員) | `woow_service_hub.woow_service_hub_group_user` | `base.user_root`, `base.user_admin` |

**Hierarchy:** Portal (`base.group_portal`) < User (`woow_service_hub_group_user`, implies `base.group_user`) < Admin (`woow_service_hub_group_admin`, implies User)

### 3.3 ACL Matrix (`ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_woow_service_user,woow.service.user,model_woow_service,woow_service_hub_group_user,1,0,0,0
access_woow_service_admin,woow.service.admin,model_woow_service,woow_service_hub_group_admin,1,1,1,1
access_woow_service_category_user,woow.service.category.user,model_woow_service_category,woow_service_hub_group_user,1,0,0,0
access_woow_service_category_admin,woow.service.category.admin,model_woow_service_category,woow_service_hub_group_admin,1,1,1,1
access_woow_service_portal,woow.service.portal,model_woow_service,base.group_portal,1,0,0,0
```

**Summary table:**

| Group | `woow.service` | `woow.service.category` |
|-------|----------------|-------------------------|
| Portal (`base.group_portal`) | R--- | ---- (no access) |
| User (`woow_service_hub_group_user`) | R--- | R--- |
| Admin (`woow_service_hub_group_admin`) | RWCD | RWCD |

### 3.4 Record Rules

| XML ID | Name | Model | Domain | Groups | R | W | C | D |
|--------|------|-------|--------|--------|---|---|---|---|
| `woow_service_hub.woow_service_portal_rule` | Portal: shared services only | `woow.service` | `[('share_partner_ids', 'in', [user.partner_id.id])]` | `base.group_portal` | Y | N | N | N |
| `woow_service_hub.woow_service_user_rule` | User: read all services | `woow.service` | `[(1, '=', 1)]` | `woow_service_hub_group_user` | Y | N | N | N |
| `woow_service_hub.woow_service_admin_rule` | Admin: full access | `woow.service` | `[(1, '=', 1)]` | `woow_service_hub_group_admin` | Y | Y | Y | Y |

### 3.5 Portal Access Pattern

The portal controller uses `.sudo()` to bypass ACLs, then manually filters by `share_partner_ids` in the search domain. This is the standard Odoo portal pattern:

```python
services = request.env["woow.service"].sudo().search([
    ("share_partner_ids", "in", [partner.id])
])
```

The record rule `woow_service_portal_rule` provides defense-in-depth at the ORM level, ensuring portal users cannot access unshared services even via direct JSON-RPC calls.

---

## 4. VIEW ARCHITECTURE

### 4.1 View Registry

| XML ID | Model | Type | Key Features |
|--------|-------|------|--------------|
| `woow_service_hub.woow_service_view_kanban` | `woow.service` | `kanban` | `class="o_kanban_mobile"`, `highlight_color="color"`, `<t t-name="card">` with `<aside>` + `<main>`, logo/icon/initial fallback |
| `woow_service_hub.woow_service_view_form` | `woow.service` | `form` | Header button, `oe_avatar` logo, notebook tabs (General/Sharing/Notes), `<chatter/>` |
| `woow_service_hub.woow_service_view_list` | `woow.service` | `list` | Uses Odoo 18 `<list>` tag (not `<tree>`) |
| `woow_service_hub.woow_service_view_search` | `woow.service` | `search` | Fields: name, category_ids, internal_manager_id, url. Group By: Category, Internal Manager |
| `woow_service_hub.woow_service_category_view_list` | `woow.service.category` | `list` | `editable="bottom"`, inline editing |
| `woow_service_hub.woow_service_category_view_form` | `woow.service.category` | `form` | Simple: name + color |

### 4.2 Actions

| XML ID | Model | `view_mode` | Search View |
|--------|-------|-------------|-------------|
| `woow_service_hub.woow_service_action` | `woow.service` | `kanban,list,form` | `woow_service_view_search` |
| `woow_service_hub.woow_service_category_action` | `woow.service.category` | `list,form` | _(default)_ |

### 4.3 Kanban Card Layout

```
+--------------------------------------------------+
| <aside>              | <main>                     |
|  [Logo 90x90]        |  Service Name (fs-5, bold) |
|  OR [FA Icon 90x90]  |  [Category Tags w/ colors] |
|  OR [Initial 90x90]  |  Manager (if set)          |
|                       |  [Open Service] btn-primary|
+--------------------------------------------------+
```

**Logo/Icon/Initial fallback priority (in Kanban):**
1. `record.logo.raw_value` is truthy -> render `<field name="logo" widget="image">`
2. `record.icon.value` is truthy -> render `<i class="fa #{record.icon.value}"/>` inside a 90x90 bg-100 box
3. Neither -> render first letter of name, uppercased, white text on `#00897B` background

### 4.4 Form Notebook Tabs

| Tab Name | Field | Notes |
|----------|-------|-------|
| General (一般) | `description` (Html) | Public description shown on portal |
| Sharing (共享) | `share_partner_ids` (many2many_tags) | Select partners to share with |
| Notes (備註) | `notes` (Text) | Internal only, not shown on portal |

### 4.5 Search View Filters/Groups

| Type | Name Attr | String | Domain/Context |
|------|-----------|--------|----------------|
| Field | - | name | Searchable |
| Field | - | category_ids | Searchable |
| Field | - | internal_manager_id | Searchable |
| Field | - | url | Searchable |
| Group By | `group_category` | Category (分類) | `{'group_by': 'category_ids'}` |
| Group By | `group_manager` | Internal Manager (內部負責人) | `{'group_by': 'internal_manager_id'}` |

### 4.6 Menu Structure

```
Service Hub (服務中心)                         [woow_service_hub.woow_service_hub_menu_root]
  sequence=200, web_icon=woow_service_hub,static/description/icon.png
  ├── All Services (所有服務)                   [woow_service_hub.woow_service_hub_menu_services]
  │   sequence=10, action=woow_service_action, groups=woow_service_hub_group_user
  └── Categories (分類)                        [woow_service_hub.woow_service_hub_menu_categories]
      sequence=20, action=woow_service_category_action, groups=woow_service_hub_group_admin
```

---

## 5. PORTAL INTEGRATION

### 5.1 Controller

| Class | Parent | File |
|-------|--------|------|
| `WoowServicePortal` | `odoo.addons.portal.controllers.portal.CustomerPortal` | `controllers/portal.py` |

### 5.2 Routes

| Route | Method Name | `type` | `auth` | `website` | Description |
|-------|-------------|--------|--------|-----------|-------------|
| `/my/services` | `portal_my_services` | `http` | `user` | `True` | Card grid of services shared with current user |
| `/my/services/<int:service_id>` | `portal_my_service_detail` | `http` | `user` | `True` | Detail page with description, open button, chatter |

### 5.3 Home Portal Integration

**Method override:** `_prepare_home_portal_values(self, counters)`

```python
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
```

### 5.4 Portal Templates

| XML ID | Name | Inherits | Purpose |
|--------|------|----------|---------|
| `woow_service_hub.portal_my_home_service` | Show Services | `portal.portal_my_home` | Adds "Services" entry to portal home sidebar via `portal.portal_docs_entry` |
| `woow_service_hub.portal_my_services_breadcrumbs` | Service Breadcrumbs | `portal.portal_breadcrumbs` | Adds breadcrumbs: "Services" or "Services > {service.name}" |
| `woow_service_hub.portal_my_services` | My Services | _(standalone)_ | Card grid layout, iterates `services`, calls `portal.portal_layout` |
| `woow_service_hub.portal_my_service_detail` | Service Detail | _(standalone)_ | Detail page with logo, description, open button, chatter (`portal.message_thread`) |

### 5.5 Portal Home Entry (`portal.portal_docs_entry` params)

```xml
<t t-set="icon" t-value="'/woow_service_hub/static/src/img/service-hub.svg'"/>
<t t-set="title">Services</t>
<t t-set="url" t-value="'/my/services'"/>
<t t-set="text">Browse services shared with you</t>
<t t-set="placeholder_count" t-value="'service_count'"/>
```

### 5.6 Detail Page: Portal Chatter

```xml
<t t-call="portal.message_thread">
    <t t-set="object" t-value="service"/>
</t>
```

Controller provides chatter context:
```python
service._portal_ensure_token()
values.update({
    "token": service.access_token,
    "pid": partner.id,
    "hash": "",
})
```

### 5.7 Detail Page: Backend Edit Link

```xml
<t t-set="o_portal_fullwidth_alert" groups="woow_service_hub.woow_service_hub_group_user">
    <t t-call="portal.portal_back_in_edit_mode">
        <t t-set="backend_url" t-value="'/odoo/woow-service/%s' % service.id"/>
    </t>
</t>
```

### 5.8 Portal Access Control Flow

1. User hits `/my/services/<id>`.
2. Controller calls `.sudo().search([("id", "=", service_id), ("share_partner_ids", "in", [partner.id])], limit=1)`.
3. If no service found (not shared), redirect to `/my`.
4. If found, render detail template.
5. Record rule `woow_service_portal_rule` provides ORM-level backup.

---

## 6. FRONTEND ASSETS

### 6.1 Asset Bundles

```python
"assets": {
    "web.assets_frontend": [
        "woow_service_hub/static/src/css/portal.css",
    ],
},
```

### 6.2 CSS Classes

| Class | Element | Purpose |
|-------|---------|---------|
| `.woow_service_card_grid` | `<div>` | CSS Grid container: `repeat(auto-fill, minmax(280px, 1fr))`, gap `1rem` |
| `.woow_service_card` | `<div>` | Flexbox row card: border `#dee2e6`, border-radius `0.5rem`, hover shadow |
| `.woow_service_card_avatar` | `<div>` | Logo/icon/initial container |
| `.woow_service_card_body` | `<div>` | `flex: 1`, title text |
| `.woow_service_card_title` | `<a>` | `font-weight: 600`, text-overflow ellipsis, hover color `#00897B` |
| `.woow_service_card_action` | `<div>` | `flex-shrink: 0`, contains Open button |
| `.woow_service_card_icon` | `<span>` | FA icon fallback container |
| `.woow_service_card_initial` | `<span>` | Name initial fallback container |
| `.woow_service_description` | `<div>` | Detail page: `img { max-width: 100% }` |

### 6.3 Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| `> 576px` | Multi-column grid: `repeat(auto-fill, minmax(280px, 1fr))` |
| `<= 576px` | Single column: `grid-template-columns: 1fr` |

### 6.4 Card Hover Effect

```css
.woow_service_card:hover {
    box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}
```

### 6.5 Brand Color

- Primary accent: `#00897B` (teal) -- used for initial fallback background and title hover color

---

## 7. DEMO DATA CATALOG

### 7.1 Categories (10 total)

| XML ID | Name | Color |
|--------|------|-------|
| `woow_service_hub.category_communication` | Communication | 1 |
| `woow_service_hub.category_project_mgmt` | Project Management | 2 |
| `woow_service_hub.category_design` | Design | 3 |
| `woow_service_hub.category_dev_tools` | DevOps / Dev Tools | 4 |
| `woow_service_hub.category_cloud` | Cloud / Infra | 5 |
| `woow_service_hub.category_analytics` | Analytics | 6 |
| `woow_service_hub.category_storage` | Storage / Docs | 7 |
| `woow_service_hub.category_finance` | Finance | 8 |
| `woow_service_hub.category_security` | Security | 9 |
| `woow_service_hub.category_hr` | HR / People | 10 |

### 7.2 Services (18 total)

| # | XML ID | Name | Icon | Color | URL | Categories | Has Logo | Has Icon | Notes |
|---|--------|------|------|-------|-----|------------|----------|----------|-------|
| 1 | `service_slack` | Slack | `fa-slack` | 4 | `woowtech.slack.com` | Communication | No | Yes | Active, has notes |
| 2 | `service_github` | GitHub | `fa-github` | 10 | `github.com/woowtech` | DevOps / Dev Tools | No | Yes | Active |
| 3 | `service_figma` | Figma | `fa-paint-brush` | 3 | `figma.com` | Design | No | Yes | Active |
| 4 | `service_jira` | Jira | `fa-tasks` | 2 | `woowtech.atlassian.net` | Project Management | No | Yes | Active |
| 5 | `service_google_workspace` | Google Workspace | `fa-google` | 1 | `workspace.google.com` | Communication, Storage / Docs | No | Yes | Active |
| 6 | `service_aws` | AWS Console | `fa-cloud` | 5 | `console.aws.amazon.com` | Cloud / Infra | No | Yes | Active |
| 7 | `service_grafana` | Grafana | `fa-line-chart` | 6 | `grafana.woowtech.com` | Analytics, DevOps / Dev Tools | No | Yes | Active |
| 8 | `service_notion` | Notion | `fa-file-text-o` | 7 | `notion.so` | Storage / Docs, Project Management | No | Yes | Trial |
| 9 | `service_1password` | 1Password | `fa-lock` | 9 | `woowtech.1password.com` | Security | No | Yes | Active |
| 10 | `service_linear` | Linear | `fa-bolt` | 2 | `linear.app` | Project Management | No | Yes | Trial |
| 11 | `service_sentry` | Sentry | `fa-bug` | 4 | `woowtech.sentry.io` | DevOps / Dev Tools | No | Yes | Active |
| 12 | `service_hackmd` | HackMD | `fa-pencil-square-o` | 7 | `hackmd.io` | Storage / Docs | No | Yes | Planned |
| 13 | `service_odoo` | Odoo ERP | `fa-building` | 8 | `localhost:9103` | Finance, HR / People | No | Yes | Active |
| 14 | `service_trello` | Trello | `fa-trello` | 2 | `trello.com` | Project Management | No | Yes | Retired |
| 15 | `service_heroku` | Heroku | `fa-server` | 5 | `dashboard.heroku.com` | Cloud / Infra | No | Yes | Retired |
| 16 | `service_n8n` | n8n Automation | _(none)_ | 4 | `n8n.woowtech.com` | DevOps / Dev Tools | No | **No** | Tests initial fallback |
| 17 | `service_miro` | Miro | _(none)_ | 3 | `miro.com` | Design, Project Management | No | **No** | Tests initial fallback |
| 18 | `service_tailscale` | Tailscale | `fa-shield` | 9 | _(none)_ | Security, Cloud / Infra | No | Yes | **No URL** -- tests UserError |

**Special test data points:**
- Services 16 & 17 have no icon -- verifies name-initial fallback rendering
- Service 18 has no URL -- verifies `UserError` from `action_open_service()`

---

## 8. I18N

### 8.1 Translation Files

| File | Locale | Status |
|------|--------|--------|
| `i18n/woow_service_hub.pot` | _(template)_ | Complete -- 50+ translatable strings |
| `i18n/zh_TW.po` | zh_TW (Traditional Chinese / 繁體中文) | Complete -- all strings translated |

### 8.2 Key Translated Strings

| English (msgid) | zh_TW (msgstr) | Context |
|-----------------|----------------|---------|
| Service Hub | 服務中心 | Module category, root menu |
| All Services | 所有服務 | Menu item |
| Categories | 分類 | Menu item, field label |
| Service Name | 服務名稱 | Field label |
| Service URL | 服務網址 | Field label |
| Full URL | 完整網址 | Field label |
| Font Awesome Icon | 圖示 | Field label |
| Card Color | 卡片顏色 | Field label |
| Internal Manager | 內部負責人 | Field label |
| Internal Notes | 內部備註 | Field label |
| Shared With | 共享對象 | Field label |
| Description | 描述 | Field label |
| Open Service | 開啟服務 | Button text |
| Sharing | 共享 | Notebook tab |
| General | 一般 | Notebook tab |
| Notes | 備註 | Notebook tab |
| Administrator | 管理員 | Group name |
| User | 使用者 | Group name |
| Services | 服務 | Portal, breadcrumb |
| Browse services shared with you | 瀏覽與您共享的服務 | Portal home text |
| No services have been shared with you yet. | 目前尚無共享的服務。 | Portal empty state |
| No URL configured for this service. | 此服務未設定網址。 | UserError message |
| Category name must be unique! | 分類名稱不可重複！ | SQL constraint message |
| Back to Services | 返回服務列表 | Portal detail page |

---

## 9. COMMON QUERIES (FAQ for LLMs)

### Q: How do I add a new service?

1. Navigate to **Service Hub > All Services** (requires User or Admin group).
2. Click **New** (requires Admin group).
3. Fill in:
   - **Service Name** (required)
   - **Service URL** (e.g. `slack.com` -- https is auto-prepended)
   - **Logo** (upload image, max 256x256) OR **Font Awesome Icon** (e.g. `fa-rocket`)
   - **Categories** (select/create tags)
   - **Internal Manager** (select from `hr.employee`)
4. In the **Sharing** tab, add portal contacts to **Shared With**.
5. In the **General** tab, add a public **Description** (shown on portal).
6. In the **Notes** tab, add **Internal Notes** (admin-only, not shown on portal).
7. Click **Save**. The service appears in the Kanban view.

### Q: How do I share a service with a portal user?

1. Open the service form as an Admin.
2. Go to the **Sharing** tab.
3. In the **Shared With** field, add the portal user's `res.partner` record.
4. Save. The portal user will now see this service at `/my/services`.

Technically: `share_partner_ids` is a Many2many to `res.partner`. The portal record rule `woow_service_portal_rule` uses domain `[('share_partner_ids', 'in', [user.partner_id.id])]`.

### Q: How does the 3-level permission system work?

**Level 1 -- Admin** (`woow_service_hub_group_admin`):
- Full CRUD on `woow.service` and `woow.service.category`
- Implies User group
- Can manage categories (submenu visible)
- Default: `base.user_root` and `base.user_admin`

**Level 2 -- User** (`woow_service_hub_group_user`):
- Read-only on `woow.service` and `woow.service.category`
- Implies `base.group_user` (internal user)
- Can see All Services menu but cannot edit
- Can call `action_open_service()` (read-only action)

**Level 3 -- Portal** (`base.group_portal`):
- Read-only on `woow.service` only (no category access)
- Record rule limits to services where `share_partner_ids` includes user's partner
- Accesses via `/my/services` portal routes
- Cannot access backend at all

### Q: What happens when a user clicks "Open Service"?

1. Button calls `action_open_service()` on the `woow.service` record.
2. Method calls `self.ensure_one()`.
3. Checks `self.full_url` -- if falsy, raises `UserError(_("No URL configured for this service."))`.
4. Returns `{"type": "ir.actions.act_url", "url": self.full_url, "target": "new"}`.
5. Odoo web client opens the URL in a new browser tab.

### Q: How does the logo/icon/initial fallback work?

**Priority order (checked at render time in QWeb):**

| Priority | Condition | Rendering |
|----------|-----------|-----------|
| 1 | `logo` field has data | `<field name="logo" widget="image">` or `<img src="/web/image/...">` |
| 2 | `icon` field has value | `<i class="fa {icon}"/>` inside styled container |
| 3 | Neither | First character of `name`, uppercased, white text on `#00897B` background |

This applies in three contexts with slightly different markup:
- **Kanban card**: 90x90px containers
- **Portal card grid**: 64x64px containers
- **Portal detail page**: 96x96px containers

### Q: What URL auto-completion logic is used?

The `_compute_full_url` method:
1. Takes `rec.url`, defaults to empty string if falsy.
2. Strips leading/trailing whitespace.
3. If non-empty and does NOT start with `http://` or `https://`, prepends `https://`.
4. Sets `rec.full_url` to the result.

**Important**: `full_url` is `store=False` (computed on-the-fly, not stored in DB).

### Q: How is portal access controlled?

**Defense in depth (two layers):**

1. **Controller layer** (`controllers/portal.py`):
   - Uses `.sudo()` to bypass ACLs.
   - Manually adds domain filter `("share_partner_ids", "in", [partner.id])`.
   - If service not found (not shared or doesn't exist), redirects to `/my`.

2. **ORM layer** (`security/woow_service_hub_rules.xml`):
   - Record rule `woow_service_portal_rule` applies domain `[('share_partner_ids', 'in', [user.partner_id.id])]` for `base.group_portal`.
   - This prevents portal users from reading unshared services even via direct JSON-RPC calls.

### Q: What Odoo 18 syntax changes are used?

| Feature | Old Syntax | Odoo 18 Syntax | Used In |
|---------|-----------|----------------|---------|
| List view | `<tree>` | `<list>` | `woow_service_view_list`, `woow_service_category_view_list` |
| Kanban card | `<t t-name="kanban-box">` | `<t t-name="card">` | `woow_service_view_kanban` |
| Kanban layout | manual divs | `<aside>` + `<main>` | `woow_service_view_kanban` |
| Chatter | `<div class="oe_chatter">...` | `<chatter/>` | `woow_service_view_form` |
| Portal home count | `_prepare_home_portal_values(counters)` | Same (stable API) | `controllers/portal.py` |

### Q: How to add a new field to the service model?

1. Add field definition in `models/woow_service.py` inside `WoowService` class.
2. If the field should appear in backend views, update relevant XML files in `views/`.
3. If the field should appear on portal, update `views/portal_templates.xml`.
4. If the field needs i18n, run `./odoo-bin --modules=woow_service_hub --i18n-export=...` and update `.po` files.
5. Upgrade the module: `./odoo-bin -u woow_service_hub -d <database>`.

### Q: How to add a new category?

**Via backend UI (Admin only):**
1. Go to **Service Hub > Categories**.
2. Type new category name in the inline editable list.
3. Pick a color index.
4. Save.

**Via XML demo data:**
```xml
<record id="category_my_new_cat" model="woow.service.category">
    <field name="name">My New Category</field>
    <field name="color">11</field>
</record>
```

**Via Python/RPC:**
```python
self.env["woow.service.category"].create({"name": "My New Cat", "color": 11})
```

---

## 10. CODE ARCHITECTURE

### 10.1 File-by-File Description

```
woow_service_hub/
├── __init__.py                          # Imports controllers/ and models/
├── __manifest__.py                      # Module metadata, depends, data files, assets
├── controllers/
│   ├── __init__.py                      # Imports portal module
│   └── portal.py                        # WoowServicePortal controller (CustomerPortal subclass)
├── demo/
│   └── demo_data.xml                    # 10 categories + 18 services demo data
├── i18n/
│   ├── woow_service_hub.pot             # POT template (50+ strings)
│   └── zh_TW.po                         # Traditional Chinese translations
├── models/
│   ├── __init__.py                      # Imports woow_service_category, then woow_service
│   ├── woow_service_category.py         # WoowServiceCategory model (name, color, unique constraint)
│   └── woow_service.py                  # WoowService model (all fields, compute, actions)
├── security/
│   ├── woow_service_hub_groups.xml      # Module category + User/Admin groups
│   ├── ir.model.access.csv              # ACL: 5 rules (User/Admin/Portal x models)
│   └── woow_service_hub_rules.xml       # Record rules: portal, user, admin
├── static/
│   ├── description/
│   │   └── icon.png                     # Module icon for app drawer
│   └── src/
│       ├── css/
│       │   └── portal.css               # Portal card grid styles (60 lines)
│       └── img/
│           └── service-hub.svg          # Portal sidebar icon
└── views/
    ├── portal_templates.xml             # 4 templates: home entry, breadcrumbs, list, detail
    ├── woow_service_category_views.xml  # Category: list (editable) + form + action
    ├── woow_service_hub_menus.xml       # 3 menuitems: root, services, categories
    └── woow_service_views.xml           # Service: kanban, form, list, search, action
```

### 10.2 Import Chain

```
__init__.py
├── from . import controllers
│   └── controllers/__init__.py
│       └── from . import portal          → controllers/portal.py
└── from . import models
    └── models/__init__.py
        ├── from . import woow_service_category  → models/woow_service_category.py
        └── from . import woow_service           → models/woow_service.py
```

**Import order matters:** `woow_service_category` must import before `woow_service` because `woow_service` references `woow.service.category` as a comodel.

### 10.3 XML Loading Order

Defined in `__manifest__.py` `data` key:

```python
"data": [
    # 1. security — groups must load before ACL and rules
    "security/woow_service_hub_groups.xml",    # Creates groups first
    "security/ir.model.access.csv",            # References groups by XML ID
    "security/woow_service_hub_rules.xml",     # References groups + model
    # 2. views
    "views/woow_service_category_views.xml",   # Category views + action
    "views/woow_service_views.xml",            # Service views + action
    "views/woow_service_hub_menus.xml",        # Menus reference actions
    # 3. portal
    "views/portal_templates.xml",              # Portal templates (last)
],
```

**Why order matters:**
- `groups.xml` must load before `ir.model.access.csv` because ACL rows reference group XML IDs.
- `ir.model.access.csv` must load before `rules.xml` because rules reference groups.
- View XMLs must load before `menus.xml` because menus reference `action` attributes.
- `portal_templates.xml` loads last because it inherits from `portal.portal_my_home` (external dependency).

---

## 11. DEPLOYMENT NOTES

### 11.1 Container Environment

| Parameter | Value |
|-----------|-------|
| Odoo container name | `odoo-saasmanage-web` |
| PostgreSQL container name | `odoo-saasmanage-db` |
| Port mapping | `9104:8069` (host:container) |
| Database name | `odoosaasmanage` |
| DB user | `odoosaasmanage` |
| DB password | `odoosaasmanage` |
| Odoo admin login | `admin` |
| Odoo admin password | `admin` |

### 11.2 Module Installation

```bash
# Copy module into addons path
docker cp woow_service_hub/ odoo-saasmanage-web:/mnt/extra-addons/

# Update module list and install
docker exec odoo-saasmanage-web odoo -d odoosaasmanage -u woow_service_hub --stop-after-init

# Or install via UI: Settings > Apps > Update Apps List > Search "Service Hub" > Install
```

### 11.3 Upgrade After Code Changes

```bash
docker exec odoo-saasmanage-web odoo -d odoosaasmanage -u woow_service_hub --stop-after-init
```

Or restart with `-u`:
```bash
docker restart odoo-saasmanage-web
```

---

## 12. TESTING REFERENCE

### 12.1 Test Suites

| File | Type | Test Count (approx.) | Description |
|------|------|----------------------|-------------|
| `tests/test_api.py` | JSON-RPC API | ~53 checks | Authentication, CRUD, permissions, edge cases, chatter |
| `tests/test_playwright.py` | HTTP/UI simulation | ~62 checks | Admin UI, user read-only, portal flow, security, XSS, injection |

**Total: ~115 test checks across 2 suites.**

### 12.2 Test Accounts

| Login | Password | Role | Purpose |
|-------|----------|------|---------|
| `admin` | `admin` | Admin group | Full CRUD tests |
| `testuser` | `testuser` | User group | Read-only permission tests |
| `portal` | `portal` | Portal group | Portal access + shared service tests |

### 12.3 Test Infrastructure

```python
BASE = "http://localhost:9104"
DB = "odoosaasmanage"
```

Tests use raw `urllib.request` for JSON-RPC calls (no external dependencies).

### 12.4 Key Test Scenarios

**Round 1 (API tests -- `test_api.py`):**
1. Authentication: valid login returns uid, bad password returns False
2. Setup: assign admin group to admin user
3. CRUD Categories: create, read, update, delete, verify deletion
4. CRUD Services: create, read full_url computation, update URL, archive, unarchive, delete
5. `action_open_service`: returns `ir.actions.act_url` for Slack, raises error for Tailscale (no URL)
6. Setup test users: create testuser (User group) and portal user
7. Permission -- User: can read, CANNOT create/delete services or categories
8. Permission -- Portal: sees only shared services, CANNOT create, CANNOT read categories
9. Edge cases: http:// preservation, URL whitespace trimming, duplicate category name
10. Chatter: message_post, read message back, access_token via portal.mixin

**Rounds 2-5 (UI/Security tests -- `test_playwright.py`):**
- Round 2: Admin UI -- login page, kanban data loading, form view, category list, menu structure, CRUD via web
- Round 3: User read-only -- can read, CANNOT write/delete, can call action_open_service
- Round 4: Portal flow -- /my page, /my/services shows shared services only, detail page, access control for unshared, chatter div validation, portal message posting
- Round 5: Security -- unauthenticated redirect, portal backend restriction, portal RPC field exposure, SQL injection prevention, XSS prevention, required field validation, archive/unarchive, CSS class presence, concurrent sessions with correct data scoping

---

## 13. ODOO 18 COMPATIBILITY NOTES

### 13.1 View Syntax Changes

```xml
<!-- Odoo 18: use <list> not <tree> -->
<list>
    <field name="name"/>
</list>

<!-- Odoo 18: Kanban uses <t t-name="card"> with semantic <aside>/<main> -->
<kanban>
    <templates>
        <t t-name="card" class="flex-row">
            <aside>...</aside>
            <main>...</main>
        </t>
    </templates>
</kanban>

<!-- Odoo 18: simplified chatter -->
<chatter/>
```

### 13.2 Portal Controller Signature

```python
# Odoo 18 signature -- counters parameter is required
def _prepare_home_portal_values(self, counters):
    values = super()._prepare_home_portal_values(counters)
    ...
```

### 13.3 Kanban Highlighting

```xml
<!-- Odoo 18: highlight_color attribute on <kanban> element -->
<kanban class="o_kanban_mobile" highlight_color="color">
```

---

## 14. QUICK REFERENCE CHEAT SHEET

### XML IDs -- Complete List

**Security:**
- `woow_service_hub.module_category_woow_service_hub`
- `woow_service_hub.woow_service_hub_group_user`
- `woow_service_hub.woow_service_hub_group_admin`
- `woow_service_hub.woow_service_portal_rule`
- `woow_service_hub.woow_service_user_rule`
- `woow_service_hub.woow_service_admin_rule`

**Views:**
- `woow_service_hub.woow_service_view_kanban`
- `woow_service_hub.woow_service_view_form`
- `woow_service_hub.woow_service_view_list`
- `woow_service_hub.woow_service_view_search`
- `woow_service_hub.woow_service_category_view_list`
- `woow_service_hub.woow_service_category_view_form`

**Actions:**
- `woow_service_hub.woow_service_action`
- `woow_service_hub.woow_service_category_action`

**Menus:**
- `woow_service_hub.woow_service_hub_menu_root`
- `woow_service_hub.woow_service_hub_menu_services`
- `woow_service_hub.woow_service_hub_menu_categories`

**Portal Templates:**
- `woow_service_hub.portal_my_home_service`
- `woow_service_hub.portal_my_services_breadcrumbs`
- `woow_service_hub.portal_my_services`
- `woow_service_hub.portal_my_service_detail`

**Demo Categories (10):**
- `woow_service_hub.category_communication`
- `woow_service_hub.category_project_mgmt`
- `woow_service_hub.category_dev_tools`
- `woow_service_hub.category_design`
- `woow_service_hub.category_cloud`
- `woow_service_hub.category_analytics`
- `woow_service_hub.category_storage`
- `woow_service_hub.category_security`
- `woow_service_hub.category_hr`
- `woow_service_hub.category_finance`

**Demo Services (18):**
- `woow_service_hub.service_slack`
- `woow_service_hub.service_github`
- `woow_service_hub.service_figma`
- `woow_service_hub.service_jira`
- `woow_service_hub.service_google_workspace`
- `woow_service_hub.service_aws`
- `woow_service_hub.service_grafana`
- `woow_service_hub.service_notion`
- `woow_service_hub.service_1password`
- `woow_service_hub.service_linear`
- `woow_service_hub.service_sentry`
- `woow_service_hub.service_hackmd`
- `woow_service_hub.service_odoo`
- `woow_service_hub.service_trello`
- `woow_service_hub.service_heroku`
- `woow_service_hub.service_n8n`
- `woow_service_hub.service_miro`
- `woow_service_hub.service_tailscale`

### Database Tables

| Model | Table Name |
|-------|------------|
| `woow.service` | `woow_service` |
| `woow.service.category` | `woow_service_category` |
| M2M: service-category | `woow_service_category_rel` |
| M2M: service-partner (sharing) | `woow_service_share_partner_rel` |

### Key Python Imports

```python
# Model file
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Controller file
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
```
