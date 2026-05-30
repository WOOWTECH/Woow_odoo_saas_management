# Service Hub Card Redesign

## Goal

Redesign the `/my/services` hub page cards to match the Odoo native portal style used by the Home Assistant hub (`/my/ha`).

## Current State

Cards use Bootstrap `card` component with:
- 48x48 icon, service name + category badges, blue `btn-primary` "Open" button
- Not using Odoo portal classes (`o_portal_docs`, `o_portal_index_card`, etc.)

## Target Design

Adopt the HA hub pattern with these additions:

### Card Structure

```xml
<div class="o_portal_docs row g-2">
  <div class="o_portal_index_card col-md-6 col-lg-4">
    <a href="/my/services/{id}" class="d-flex gap-2 gap-md-3 py-3 pe-2 px-md-3 h-100 rounded text-decoration-none bg-100">
      <div class="o_portal_icon d-block align-self-start">
        <!-- 64x64 icon/logo/initial -->
      </div>
      <div class="flex-grow-1">
        <div class="mt-0 mb-1 fs-5 fw-normal lh-1">Service Name</div>
        <div class="opacity-75">
          <span class="badge text-bg-light">Category</span>
        </div>
      </div>
      <a href="external_url" target="_blank" class="btn btn-outline-secondary btn-sm align-self-center flex-shrink-0" onclick="event.stopPropagation();">
        <i class="fa fa-external-link me-1"/>Open
      </a>
    </a>
  </div>
</div>
```

### Key Decisions

1. **Outer element**: `<a>` tag wrapping entire card (clickable to detail page)
2. **Icon**: 64x64, using `o_portal_icon` class
3. **Categories**: Odoo native `badge text-bg-light` below service name
4. **Open button**: `btn btn-outline-secondary btn-sm` (not blue primary), with `event.stopPropagation()` to prevent card click
5. **Background**: `bg-100` (Odoo light gray, matching HA hub)

### Files to Modify

- `woow_service_hub/views/portal_templates.xml` — `portal_my_services` template only
