#!/usr/bin/env python3
"""
Round 1: Backend API tests for woow_service_hub via Odoo JSON-RPC.
Tests: authentication, CRUD, permissions (admin/user/portal), edge cases.
"""
import json
import sys
import urllib.request

BASE = "http://localhost:9104"
DB = "odoosaasmanage"

PASS = 0
FAIL = 0
ERRORS = []


def rpc(url, method, params):
    """Low-level JSON-RPC call."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def authenticate(login, password):
    """Authenticate and return uid + session."""
    result = rpc(f"{BASE}/web/session/authenticate", "call", {
        "db": DB, "login": login, "password": password,
    })
    uid = result.get("result", {}).get("uid")
    return uid


def call_model(model, method, args=None, kwargs=None, login="admin", password="admin"):
    """Call a model method via JSON-RPC dataset/call_kw."""
    # First authenticate to get a session cookie
    payload_auth = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {"db": DB, "login": login, "password": password},
    }).encode()
    req_auth = urllib.request.Request(
        f"{BASE}/web/session/authenticate",
        data=payload_auth,
        headers={"Content-Type": "application/json"},
    )
    resp_auth = urllib.request.urlopen(req_auth)
    cookies = resp_auth.headers.get("Set-Cookie", "")
    session_id = ""
    for part in cookies.split(";"):
        part = part.strip()
        if part.startswith("session_id="):
            session_id = part
            break

    # Now call the model
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "call",
        "params": {
            "model": model,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        },
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/web/dataset/call_kw",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Cookie": session_id,
        },
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        msg = f"  FAIL: {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        ERRORS.append(name)


def get_session(login, password):
    """Get a session cookie string."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {"db": DB, "login": login, "password": password},
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/web/session/authenticate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    uid = data.get("result", {}).get("uid")
    cookies = resp.headers.get("Set-Cookie", "")
    session_id = ""
    for part in cookies.split(";"):
        part = part.strip()
        if part.startswith("session_id="):
            session_id = part
            break
    return uid, session_id


def rpc_with_session(session_id, model, method, args=None, kwargs=None):
    """Call model method with existing session."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "call",
        "params": {
            "model": model,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        },
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/web/dataset/call_kw",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Cookie": session_id,
        },
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "code": e.code}


# =====================================================================
print("=" * 60)
print("ROUND 1: Backend API Tests")
print("=" * 60)

# ------------------------------------------------------------------
# 1. Authentication
# ------------------------------------------------------------------
print("\n--- 1. Authentication ---")
uid = authenticate("admin", "admin")
check("Admin login returns valid uid", uid and uid > 0, f"uid={uid}")

bad_uid = authenticate("admin", "wrongpassword")
check("Bad password returns False/None", not bad_uid, f"uid={bad_uid}")

# ------------------------------------------------------------------
# 2. Setup: assign admin group to admin user
# ------------------------------------------------------------------
print("\n--- 2. Setup: Admin group assignment ---")
admin_uid, admin_session = get_session("admin", "admin")

# Find the admin group ID
result = rpc_with_session(admin_session, "ir.model.data", "search_read", [
    [["module", "=", "woow_service_hub"], ["name", "=", "woow_service_hub_group_admin"]],
    ["res_id"],
])
admin_group_data = result.get("result", [])
check("Found admin group XML ID", len(admin_group_data) > 0)

if admin_group_data:
    admin_group_id = admin_group_data[0]["res_id"]

    # Add admin to the admin group
    result = rpc_with_session(admin_session, "res.users", "write", [
        [admin_uid], {"groups_id": [(4, admin_group_id)]}
    ])
    check("Assigned admin group to admin user", result.get("result") is True)

# ------------------------------------------------------------------
# 3. CRUD: Categories
# ------------------------------------------------------------------
print("\n--- 3. CRUD: Categories ---")

# Read existing categories
result = rpc_with_session(admin_session, "woow.service.category", "search_read", [
    [], ["name", "color"],
])
categories = result.get("result", [])
check("Categories loaded from demo data", len(categories) >= 10, f"count={len(categories)}")

# Create a new category
result = rpc_with_session(admin_session, "woow.service.category", "create", [
    [{"name": "Test Category API", "color": 11}],
])
new_cat_ids = result.get("result", [])
check("Create category via API", len(new_cat_ids) == 1, f"ids={new_cat_ids}")

if new_cat_ids:
    new_cat_id = new_cat_ids[0]

    # Read it back
    result = rpc_with_session(admin_session, "woow.service.category", "read", [
        [new_cat_id], ["name", "color"],
    ])
    cat_data = result.get("result", [])
    check("Read category back", len(cat_data) == 1 and cat_data[0]["name"] == "Test Category API")

    # Update
    result = rpc_with_session(admin_session, "woow.service.category", "write", [
        [new_cat_id], {"name": "Test Category Updated"},
    ])
    check("Update category name", result.get("result") is True)

    # Verify update
    result = rpc_with_session(admin_session, "woow.service.category", "read", [
        [new_cat_id], ["name"],
    ])
    check("Verify update", result.get("result", [{}])[0].get("name") == "Test Category Updated")

    # Delete
    result = rpc_with_session(admin_session, "woow.service.category", "unlink", [
        [new_cat_id],
    ])
    check("Delete category", result.get("result") is True)

    # Verify deletion
    result = rpc_with_session(admin_session, "woow.service.category", "search", [
        [["id", "=", new_cat_id]],
    ])
    check("Verify deletion (search returns empty)", len(result.get("result", [])) == 0)

# ------------------------------------------------------------------
# 4. CRUD: Services
# ------------------------------------------------------------------
print("\n--- 4. CRUD: Services ---")

# Read existing services
result = rpc_with_session(admin_session, "woow.service", "search_read", [
    [], ["name", "url", "full_url", "active"],
])
services = result.get("result", [])
check("Services loaded from demo data", len(services) >= 18, f"count={len(services)}")

# Check full_url computation
slack = [s for s in services if s["name"] == "Slack"]
if slack:
    check("full_url computed correctly for Slack",
          slack[0]["full_url"] == "https://woowtech.slack.com",
          f"got: {slack[0]['full_url']}")

# Check service without URL (Tailscale)
tailscale = [s for s in services if s["name"] == "Tailscale"]
if tailscale:
    check("Tailscale has empty URL", not tailscale[0]["url"])
    check("Tailscale full_url is empty/False", not tailscale[0]["full_url"])

# Create a new service
result = rpc_with_session(admin_session, "woow.service", "create", [
    [{"name": "Test Service API", "url": "test.example.com"}],
])
new_svc_ids = result.get("result", [])
check("Create service via API", len(new_svc_ids) == 1)

if new_svc_ids:
    new_svc_id = new_svc_ids[0]

    # Read back — check full_url computation
    result = rpc_with_session(admin_session, "woow.service", "read", [
        [new_svc_id], ["name", "url", "full_url", "active"],
    ])
    svc_data = result.get("result", [{}])[0]
    check("Service full_url auto-prepends https",
          svc_data.get("full_url") == "https://test.example.com",
          f"got: {svc_data.get('full_url')}")
    check("Service is active by default", svc_data.get("active") is True)

    # Update URL
    result = rpc_with_session(admin_session, "woow.service", "write", [
        [new_svc_id], {"url": "https://test2.example.com"},
    ])
    check("Update service URL", result.get("result") is True)

    # Verify: full_url should keep https:// as-is (already has it)
    result = rpc_with_session(admin_session, "woow.service", "read", [
        [new_svc_id], ["full_url"],
    ])
    svc_data2 = result.get("result", [{}])[0]
    check("full_url preserves existing https",
          svc_data2.get("full_url") == "https://test2.example.com")

    # Archive (standard Odoo action_archive)
    result = rpc_with_session(admin_session, "woow.service", "action_archive", [
        [new_svc_id],
    ])
    check("Archive service", "error" not in result)

    # Verify archived
    result = rpc_with_session(admin_session, "woow.service", "read", [
        [new_svc_id], ["active"],
    ])
    check("Service is archived", result.get("result", [{}])[0].get("active") is False)

    # Unarchive
    result = rpc_with_session(admin_session, "woow.service", "action_unarchive", [
        [new_svc_id],
    ])
    check("Unarchive service", "error" not in result)

    # Delete
    result = rpc_with_session(admin_session, "woow.service", "unlink", [
        [new_svc_id],
    ])
    check("Delete service", result.get("result") is True)

# ------------------------------------------------------------------
# 5. action_open_service
# ------------------------------------------------------------------
print("\n--- 5. action_open_service ---")

# Find Slack service
result = rpc_with_session(admin_session, "woow.service", "search_read", [
    [["name", "=", "Slack"]], ["id"],
])
slack_ids = [r["id"] for r in result.get("result", [])]
if slack_ids:
    # Call action_open_service on Slack (has URL)
    result = rpc_with_session(admin_session, "woow.service", "action_open_service", [
        slack_ids[:1],
    ])
    action = result.get("result", {})
    check("action_open_service returns act_url",
          action.get("type") == "ir.actions.act_url")
    check("action_open_service target=new",
          action.get("target") == "new")
    check("action_open_service URL is correct",
          action.get("url") == "https://woowtech.slack.com",
          f"got: {action.get('url')}")

# Find Tailscale (no URL) — should raise UserError
result = rpc_with_session(admin_session, "woow.service", "search_read", [
    [["name", "=", "Tailscale"]], ["id"],
])
tailscale_ids = [r["id"] for r in result.get("result", [])]
if tailscale_ids:
    result = rpc_with_session(admin_session, "woow.service", "action_open_service", [
        tailscale_ids[:1],
    ])
    error = result.get("result", {}).get("error") or result.get("error")
    # When UserError is raised, JSON-RPC returns error in result
    has_error = "error" in result.get("result", {}) if isinstance(result.get("result"), dict) else "error" in result
    check("action_open_service raises error for empty URL", has_error,
          f"response keys: {list(result.keys())}, result type: {type(result.get('result'))}")

# ------------------------------------------------------------------
# 6. Setup test users (User role + Portal user)
# ------------------------------------------------------------------
print("\n--- 6. Setup test users ---")

# Find user group ID
result = rpc_with_session(admin_session, "ir.model.data", "search_read", [
    [["module", "=", "woow_service_hub"], ["name", "=", "woow_service_hub_group_user"]],
    ["res_id"],
])
user_group_data = result.get("result", [])
user_group_id = user_group_data[0]["res_id"] if user_group_data else None
check("Found user group XML ID", user_group_id is not None)

# Find portal group ID
result = rpc_with_session(admin_session, "ir.model.data", "search_read", [
    [["module", "=", "base"], ["name", "=", "group_portal"]],
    ["res_id"],
])
portal_group_data = result.get("result", [])
portal_group_id = portal_group_data[0]["res_id"] if portal_group_data else None
check("Found portal group XML ID", portal_group_id is not None)

# Create or find internal user with "User" group
result = rpc_with_session(admin_session, "res.users", "search_read", [
    [["login", "=", "testuser"]], ["id"],
])
existing_test_users = result.get("result", [])
if existing_test_users:
    test_user_ids = [existing_test_users[0]["id"]]
    check("Test internal user already exists", True)
else:
    result = rpc_with_session(admin_session, "res.users", "create", [
        [{
            "name": "Test User (Read-Only)",
            "login": "testuser",
            "password": "testuser",
            "groups_id": [(4, user_group_id)] if user_group_id else [],
        }],
    ])
    test_user_ids = result.get("result", [])
    check("Created test internal user", len(test_user_ids) == 1, f"ids={test_user_ids}")

# Create or find portal user
result = rpc_with_session(admin_session, "res.users", "search_read", [
    [["login", "=", "portal"]], ["id"],
])
existing_portal_users = result.get("result", [])
if existing_portal_users:
    portal_user_ids = [existing_portal_users[0]["id"]]
    check("Test portal user already exists", True)
else:
    result = rpc_with_session(admin_session, "res.users", "create", [
        [{
            "name": "Portal User",
            "login": "portal",
            "password": "portal",
            "groups_id": [(6, 0, [portal_group_id])] if portal_group_id else [],
        }],
    ])
    portal_user_ids = result.get("result", [])
    check("Created test portal user", len(portal_user_ids) == 1, f"ids={portal_user_ids}")

# Share some services with the portal user
if portal_user_ids:
    # Get portal user's partner_id
    result = rpc_with_session(admin_session, "res.users", "read", [
        portal_user_ids, ["partner_id"],
    ])
    portal_partner_id = result.get("result", [{}])[0].get("partner_id", [None])[0]

    if portal_partner_id:
        # Find Slack and GitHub service IDs
        result = rpc_with_session(admin_session, "woow.service", "search_read", [
            [["name", "in", ["Slack", "GitHub", "Figma"]]], ["id", "name"],
        ])
        share_service_ids = [r["id"] for r in result.get("result", [])]

        # Add portal partner to share_partner_ids
        for svc_id in share_service_ids:
            rpc_with_session(admin_session, "woow.service", "write", [
                [svc_id], {"share_partner_ids": [(4, portal_partner_id)]},
            ])
        check(f"Shared {len(share_service_ids)} services with portal user",
              len(share_service_ids) >= 3, f"services: {share_service_ids}")

# ------------------------------------------------------------------
# 7. Permission tests: User (read-only)
# ------------------------------------------------------------------
print("\n--- 7. Permission tests: User (read-only) ---")

test_uid, test_session = get_session("testuser", "testuser")
check("Test user can authenticate", test_uid and test_uid > 0)

if test_session:
    # User can read services
    result = rpc_with_session(test_session, "woow.service", "search_read", [
        [], ["name"],
    ])
    user_services = result.get("result", [])
    check("User can read services", len(user_services) > 0, f"count={len(user_services)}")

    # User can read categories
    result = rpc_with_session(test_session, "woow.service.category", "search_read", [
        [], ["name"],
    ])
    user_cats = result.get("result", [])
    check("User can read categories", len(user_cats) > 0, f"count={len(user_cats)}")

    # User CANNOT create a service
    result = rpc_with_session(test_session, "woow.service", "create", [
        [{"name": "Hacker Service", "state": "active"}],
    ])
    has_error = "error" in result or "error" in result.get("result", {})
    check("User CANNOT create service (AccessError)", has_error)

    # User CANNOT delete a service
    if user_services:
        result = rpc_with_session(test_session, "woow.service", "unlink", [
            [user_services[0]["id"]],
        ])
        has_error = "error" in result or "error" in result.get("result", {})
        check("User CANNOT delete service (AccessError)", has_error)

    # User CANNOT create a category
    result = rpc_with_session(test_session, "woow.service.category", "create", [
        [{"name": "Hacker Category"}],
    ])
    has_error = "error" in result or "error" in result.get("result", {})
    check("User CANNOT create category (AccessError)", has_error)

# ------------------------------------------------------------------
# 8. Permission tests: Portal user
# ------------------------------------------------------------------
print("\n--- 8. Permission tests: Portal user ---")

portal_uid, portal_session = get_session("portal", "portal")
check("Portal user can authenticate", portal_uid and portal_uid > 0)

if portal_session:
    # Portal user can read shared services
    result = rpc_with_session(portal_session, "woow.service", "search_read", [
        [], ["name"],
    ])
    portal_services = result.get("result", [])
    check("Portal user sees only shared services",
          0 < len(portal_services) <= 10,
          f"count={len(portal_services)}")

    # Portal user CANNOT read all services
    check("Portal user does NOT see all 18 services",
          len(portal_services) < 18, f"count={len(portal_services)}")

    # Portal user CANNOT create
    result = rpc_with_session(portal_session, "woow.service", "create", [
        [{"name": "Hacker Portal"}],
    ])
    has_error = "error" in result or "error" in result.get("result", {})
    check("Portal user CANNOT create service", has_error)

    # Portal user CANNOT read categories (ACL denies)
    result = rpc_with_session(portal_session, "woow.service.category", "search_read", [
        [], ["name"],
    ])
    portal_cats = result.get("result", [])
    has_error = "error" in result or "error" in result.get("result", {})
    check("Portal user CANNOT read categories",
          has_error or len(portal_cats) == 0,
          f"cats={len(portal_cats)}, has_error={has_error}")

# ------------------------------------------------------------------
# 9. Edge cases
# ------------------------------------------------------------------
print("\n--- 9. Edge cases ---")

# URL with http:// prefix — should NOT double-prepend
result = rpc_with_session(admin_session, "woow.service", "create", [
    [{"name": "HTTP Test", "url": "http://insecure.example.com"}],
])
http_ids = result.get("result", [])
if http_ids:
    result = rpc_with_session(admin_session, "woow.service", "read", [
        http_ids, ["full_url"],
    ])
    full_url = result.get("result", [{}])[0].get("full_url")
    check("http:// URL is preserved (no double prefix)",
          full_url == "http://insecure.example.com",
          f"got: {full_url}")
    rpc_with_session(admin_session, "woow.service", "unlink", [http_ids])

# URL with spaces
result = rpc_with_session(admin_session, "woow.service", "create", [
    [{"name": "Space Test", "url": "  example.com  "}],
])
space_ids = result.get("result", [])
if space_ids:
    result = rpc_with_session(admin_session, "woow.service", "read", [
        space_ids, ["full_url"],
    ])
    full_url = result.get("result", [{}])[0].get("full_url")
    check("URL with spaces gets trimmed + https prepended",
          full_url == "https://example.com",
          f"got: {full_url}")
    rpc_with_session(admin_session, "woow.service", "unlink", [space_ids])

# Duplicate category name (unique constraint)
result = rpc_with_session(admin_session, "woow.service.category", "create", [
    [{"name": "Communication"}],  # already exists in demo data
])
has_error = "error" in result or "error" in result.get("result", {})
check("Duplicate category name raises error (unique constraint)", has_error)

# ------------------------------------------------------------------
# 10. Portal chatter (mail.thread) support
# ------------------------------------------------------------------
print("\n--- 10. Portal chatter (mail.thread) ---")

# 10.1 Service model inherits mail.thread — can message_post
result = rpc_with_session(admin_session, "woow.service", "search", [
    [["name", "=", "Slack"]],
])
slack_ids = result.get("result", [])
if slack_ids:
    slack_id = slack_ids[0]

    # Admin can post a message on the service
    result = rpc_with_session(admin_session, "woow.service", "message_post", [
        [slack_id],
    ], kwargs={"body": "Admin chatter test message", "message_type": "comment"})
    msg_id = result.get("result")
    check("Admin can message_post on service",
          msg_id and not result.get("error"),
          f"msg_id={msg_id}")

    # Read message back
    if msg_id:
        result = rpc_with_session(admin_session, "mail.message", "read", [
            [msg_id], ["body", "model", "res_id"],
        ])
        msg = result.get("result", [{}])[0]
        check("Message body saved correctly",
              "Admin chatter test message" in msg.get("body", ""),
              f"body={msg.get('body', '')[:60]}")
        check("Message linked to woow.service model",
              msg.get("model") == "woow.service")
        check("Message linked to correct record",
              msg.get("res_id") == slack_id)

    # 10.2 Service has access_token via portal.mixin
    result = rpc_with_session(admin_session, "woow.service", "read", [
        [slack_id], ["access_token"],
    ])
    token = result.get("result", [{}])[0].get("access_token")
    check("Service has access_token field (portal.mixin)",
          "access_token" in result.get("result", [{}])[0],
          f"token={'present' if token else 'empty/missing'}")

    # 10.3 access_token can be generated (write empty then access_url triggers it)
    # The portal controller calls _portal_ensure_token which is a private method.
    # Verify that access_token is non-empty after being set by the system.
    if token:
        check("access_token is non-empty string",
              isinstance(token, str) and len(token) > 8,
              f"token_len={len(str(token)) if token else 0}")
    else:
        # Token might not have been generated yet; write one manually to confirm field works
        rpc_with_session(admin_session, "woow.service", "write", [
            [slack_id], {"access_token": "test-manual-token-12345"},
        ])
        result = rpc_with_session(admin_session, "woow.service", "read", [
            [slack_id], ["access_token"],
        ])
        new_token = result.get("result", [{}])[0].get("access_token")
        check("access_token field is writable and readable",
              new_token == "test-manual-token-12345",
              f"token={new_token}")
else:
    check("Slack service found for chatter tests", False, "Slack not in DB")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
if ERRORS:
    print(f"FAILURES: {', '.join(ERRORS)}")
print("=" * 60)

sys.exit(1 if FAIL else 0)
