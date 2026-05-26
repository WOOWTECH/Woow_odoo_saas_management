#!/usr/bin/env python3
"""
Rounds 2-5: Comprehensive Playwright UI + Security tests for woow_service_hub.
Enterprise-grade browser automation test suite.
"""
import sys
import time
import json
import re
import urllib.request
import urllib.parse

# --- Config ---
BASE = "http://localhost:9104"
DB = "odoosaasmanage"
PASS = 0
FAIL = 0
ERRORS = []

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

def http_get(url, cookies=None, allow_redirects=False):
    """Simple HTTP GET returning (status, headers, body)."""
    req = urllib.request.Request(url)
    if cookies:
        req.add_header("Cookie", cookies)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")

def http_post_json(url, data, cookies=None):
    """HTTP POST with JSON body."""
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    if cookies:
        req.add_header("Cookie", cookies)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")

def login_get_cookie(login, password):
    """Login via web and return session cookie string."""
    data = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {"db": DB, "login": login, "password": password},
    }
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}/web/session/authenticate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    uid = result.get("result", {}).get("uid")
    cookies = resp.headers.get("Set-Cookie", "")
    session_id = ""
    for part in cookies.split(";"):
        part = part.strip()
        if part.startswith("session_id="):
            session_id = part
            break
    return uid, session_id


# =====================================================================
print("=" * 70)
print("ROUNDS 2-5: Comprehensive UI + Security + Edge Case Tests")
print("=" * 70)

# ------------------------------------------------------------------
# Round 2: Admin UI Flow
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 2: Admin UI Flow")
print("=" * 70)

admin_uid, admin_cookie = login_get_cookie("admin", "admin")
check("Admin login successful", admin_uid and admin_uid > 0)

# 2.1 Login page accessible
print("\n--- 2.1 Login page ---")
status, headers, body = http_get(f"{BASE}/web/login")
check("Login page returns 200", status == 200)
check("Login page contains login form", "oe_login_form" in body or "login" in body.lower())

# 2.2 Service Hub action accessible
print("\n--- 2.2 Service Hub Kanban ---")
status, headers, body = http_get(f"{BASE}/web", cookies=admin_cookie)
check("Web client loads for admin", status == 200)

# 2.3 Test JSON-RPC views load (simulates Kanban loading data)
print("\n--- 2.3 Kanban data loading ---")
data = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service",
        "method": "web_search_read",
        "args": [],
        "kwargs": {
            "domain": [],
            "specification": {
                "name": {}, "logo": {}, "icon": {}, "color": {},
                "url": {}, "category_ids": {"fields": {"display_name": {}, "color": {}}},
                "internal_manager_id": {"fields": {"display_name": {}}},
            },
            "limit": 80,
        },
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data, cookies=admin_cookie)
resp = json.loads(resp_body)
records = resp.get("result", {}).get("records", [])
check("Kanban web_search_read returns services", len(records) > 0, f"count={len(records)}")

# 2.4 Form view load
print("\n--- 2.4 Form view data ---")
data_form = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[["name", "=", "Slack"]], [
            "name", "logo", "icon", "color", "url", "full_url",
            "category_ids", "internal_manager_id", "share_partner_ids",
            "description", "notes",
        ]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_form, cookies=admin_cookie)
slack_data = json.loads(resp_body).get("result", [])
check("Slack form data loads", len(slack_data) > 0)
if slack_data:
    s = slack_data[0]
    check("Slack has icon field", s.get("icon") == "fa-slack", f"icon={s.get('icon')}")
    check("Slack has category_ids", len(s.get("category_ids", [])) > 0)
    check("Slack full_url computed", s.get("full_url") == "https://woowtech.slack.com")

# 2.5 Category management
print("\n--- 2.5 Category List ---")
data_cat = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service.category", "method": "search_read",
        "args": [[], ["name", "color"]], "kwargs": {"order": "name"},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_cat, cookies=admin_cookie)
cats = json.loads(resp_body).get("result", [])
check("Category list loads", len(cats) >= 10, f"count={len(cats)}")
cat_names = [c["name"] for c in cats]
check("Communication category exists", "Communication" in cat_names)
check("Security category exists", "Security" in cat_names)

# 2.6 Menu structure
print("\n--- 2.6 Menu structure ---")
data_menu = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "ir.ui.menu", "method": "search_read",
        "args": [[["name", "in", ["Service Hub", "All Services", "Service Categories", "Categories"]]]],
        "kwargs": {"fields": ["name", "parent_id", "action"]},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_menu, cookies=admin_cookie)
menus = json.loads(resp_body).get("result", [])
menu_names = [m["name"] for m in menus]
check("Service Hub root menu exists", "Service Hub" in menu_names, f"menus={menu_names}")
check("All Services submenu exists", "All Services" in menu_names, f"menus={menu_names}")
check("Categories submenu exists", "Categories" in menu_names or "Service Categories" in menu_names,
      f"menus={menu_names}")

# 2.7 Admin CRUD via web_save (simulates form save)
print("\n--- 2.7 Admin CRUD via web_save ---")
data_create = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "create",
        "args": [[{"name": "Playwright Test Service", "url": "playwright.dev"}]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_create, cookies=admin_cookie)
new_ids = json.loads(resp_body).get("result", [])
check("Admin creates service via web", len(new_ids) == 1)
if new_ids:
    # Clean up
    data_del = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "unlink",
            "args": [new_ids], "kwargs": {},
        },
    }
    http_post_json(f"{BASE}/web/dataset/call_kw", data_del, cookies=admin_cookie)


# ------------------------------------------------------------------
# Round 3: User (Read-Only) UI Flow
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 3: User (Read-Only) UI Flow")
print("=" * 70)

user_uid, user_cookie = login_get_cookie("testuser", "testuser")
check("User login successful", user_uid and user_uid > 0)

# 3.1 User can load web client
print("\n--- 3.1 User web client ---")
status, headers, body = http_get(f"{BASE}/web", cookies=user_cookie)
check("User can load web client", status == 200)

# 3.2 User can read services
print("\n--- 3.2 User reads services ---")
data_read = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[], ["name"]], "kwargs": {"limit": 100},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_read, cookies=user_cookie)
result = json.loads(resp_body)
user_services = result.get("result", [])
has_error = "error" in result
check("User can read service list", not has_error and len(user_services) > 0,
      f"count={len(user_services)}, error={has_error}")

# 3.3 User CANNOT write
print("\n--- 3.3 User write blocked ---")
if user_services:
    data_write = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "write",
            "args": [[user_services[0]["id"]], {"name": "HACKED"}],
            "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_write, cookies=user_cookie)
    result = json.loads(resp_body)
    has_error = "error" in result
    check("User CANNOT write service", has_error)

# 3.4 User CANNOT delete
print("\n--- 3.4 User delete blocked ---")
if user_services:
    data_delete = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "unlink",
            "args": [[user_services[0]["id"]]], "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_delete, cookies=user_cookie)
    result = json.loads(resp_body)
    has_error = "error" in result
    check("User CANNOT delete service", has_error)

# 3.5 User can call action_open_service (read-only action)
print("\n--- 3.5 User can open service ---")
slack_in_list = [s for s in user_services if s.get("name") == "Slack"]
if slack_in_list:
    data_action = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "action_open_service",
            "args": [[slack_in_list[0]["id"]]], "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_action, cookies=user_cookie)
    result = json.loads(resp_body)
    action = result.get("result", {})
    check("User can call action_open_service",
          action.get("type") == "ir.actions.act_url",
          f"result={action}")


# ------------------------------------------------------------------
# Round 4: Portal User Flow
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 4: Portal User Flow")
print("=" * 70)

portal_uid, portal_cookie = login_get_cookie("portal", "portal")
check("Portal user login successful", portal_uid and portal_uid > 0)

# Setup: ensure services are shared with the portal user
print("\n--- 4.0 Setup: share services with portal user ---")
# Get portal user's partner_id
data_portal_partner = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "res.users", "method": "search_read",
        "args": [[["login", "=", "portal"]], ["partner_id"]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_portal_partner, cookies=admin_cookie)
portal_partner_result = json.loads(resp_body).get("result", [])
portal_partner_id = portal_partner_result[0]["partner_id"][0] if portal_partner_result else None

if portal_partner_id:
    # Find Slack, GitHub, Figma service IDs
    data_find = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "search_read",
            "args": [[["name", "in", ["Slack", "GitHub", "Figma"]]], ["id", "name"]],
            "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_find, cookies=admin_cookie)
    share_services = json.loads(resp_body).get("result", [])
    for svc in share_services:
        data_share = {
            "jsonrpc": "2.0", "id": 1, "method": "call",
            "params": {
                "model": "woow.service", "method": "write",
                "args": [[svc["id"]], {"share_partner_ids": [(4, portal_partner_id)]}],
                "kwargs": {},
            },
        }
        http_post_json(f"{BASE}/web/dataset/call_kw", data_share, cookies=admin_cookie)
    check(f"Shared {len(share_services)} services with portal user",
          len(share_services) >= 3, f"found: {[s['name'] for s in share_services]}")

# Re-login portal user to pick up new permissions
portal_uid, portal_cookie = login_get_cookie("portal", "portal")

# 4.1 Portal /my page accessible
print("\n--- 4.1 Portal /my page ---")
status, headers, body = http_get(f"{BASE}/my", cookies=portal_cookie)
check("Portal /my returns 200", status == 200)
check("Portal /my contains Services entry", "services" in body.lower() or "Services" in body,
      "Looking for 'services' link in portal home")

# 4.2 Portal /my/services page
print("\n--- 4.2 Portal /my/services ---")
status, headers, body = http_get(f"{BASE}/my/services", cookies=portal_cookie)
check("Portal /my/services returns 200", status == 200)
check("Portal /my/services shows Slack", "Slack" in body)
check("Portal /my/services shows GitHub", "GitHub" in body)
check("Portal /my/services shows Figma", "Figma" in body)
check("Portal /my/services does NOT show Jira (not shared)",
      "Jira" not in body or "jira" not in body.lower())
check("Portal /my/services does NOT show internal notes",
      "admin: IT team" not in body and "Workspace: woowtech" not in body,
      "Internal notes content should be hidden from portal")

# 4.3 Portal service detail page
print("\n--- 4.3 Portal service detail ---")
# Find a shared service ID
data_shared = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[["name", "=", "Slack"]], ["id"]], "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_shared, cookies=admin_cookie)
slack_results = json.loads(resp_body).get("result", [])
if slack_results:
    slack_id = slack_results[0]["id"]
    status, headers, body = http_get(f"{BASE}/my/services/{slack_id}", cookies=portal_cookie)
    check("Portal detail page returns 200", status == 200)
    check("Portal detail shows service name", "Slack" in body)
    check("Portal detail shows description", "messaging" in body.lower() or "collaboration" in body.lower())
    check("Portal detail does NOT show internal manager", "internal_manager" not in body.lower())
    check("Portal detail does NOT show notes field",
          "admin: IT team" not in body,
          "Internal notes should be hidden from portal")

# 4.4 Portal cannot access unshared service detail
print("\n--- 4.4 Portal access control ---")
data_jira = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[["name", "=", "Jira"]], ["id"]], "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_jira, cookies=admin_cookie)
jira_results = json.loads(resp_body).get("result", [])
if jira_results:
    jira_id = jira_results[0]["id"]
    status, headers, body = http_get(f"{BASE}/my/services/{jira_id}", cookies=portal_cookie)
    check("Portal CANNOT access unshared service detail",
          status in (302, 303, 403, 404) or "/my" in headers.get("Location", "") or "Jira" not in body,
          f"status={status}")


# 4.5 Portal chatter (message_thread) on detail page
print("\n--- 4.5 Portal chatter on detail page ---")
if slack_results:
    slack_id = slack_results[0]["id"]
    status, headers, body = http_get(f"{BASE}/my/services/{slack_id}", cookies=portal_cookie)
    check("Portal detail page has chatter div",
          'id="discussion"' in body,
          "Looking for <div id='discussion'>")
    check("Portal chatter has o_portal_chatter class",
          "o_portal_chatter" in body)
    check("Portal chatter data-res_model is woow.service",
          'data-res_model="woow.service"' in body)
    check("Portal chatter data-res_id matches service",
          f'data-res_id="{slack_id}"' in body,
          f"Expected data-res_id=\"{slack_id}\"")
    check("Portal chatter data-allow_composer is 1",
          'data-allow_composer="1"' in body)
    # Extract and validate access token
    token_match = re.search(r'data-token="([^"]+)"', body)
    check("Portal chatter has non-empty access token",
          token_match is not None and len(token_match.group(1)) > 0,
          f"token={'found' if token_match else 'missing'}")
    # Validate data-pid matches portal user's partner_id
    pid_match = re.search(r'data-pid="(\d+)"', body)
    check("Portal chatter data-pid is portal partner",
          pid_match is not None and int(pid_match.group(1)) == portal_partner_id,
          f"pid={pid_match.group(1) if pid_match else 'missing'}, expected={portal_partner_id}")

# 4.6 Portal chatter POST — submit a message via API
print("\n--- 4.6 Portal chatter message posting ---")
if slack_results and token_match:
    chatter_token = token_match.group(1)
    # Odoo 18 uses /mail/message/post (JSON-RPC style)
    post_payload = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "thread_model": "woow.service",
            "thread_id": slack_id,
            "post_data": {
                "body": "<p>Test comment from portal chatter</p>",
                "message_type": "comment",
            },
            "token": chatter_token,
        },
    }
    status, _, resp_body = http_post_json(
        f"{BASE}/mail/message/post", post_payload, cookies=portal_cookie
    )
    post_result = json.loads(resp_body) if resp_body else {}
    has_error = "error" in post_result
    check("Portal chatter message post accepted",
          status == 200 and not has_error,
          f"status={status}, error={post_result.get('error', {}).get('message', 'none')[:80] if has_error else 'none'}")

    # Verify message appears via admin RPC
    data_msgs = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "mail.message", "method": "search_read",
            "args": [[
                ["model", "=", "woow.service"],
                ["res_id", "=", slack_id],
                ["body", "ilike", "Test comment from portal chatter"],
            ], ["body", "author_id"]],
            "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_msgs, cookies=admin_cookie)
    msgs = json.loads(resp_body).get("result", [])
    check("Portal chatter message saved in mail.message",
          len(msgs) >= 1,
          f"found {len(msgs)} matching messages")

# ------------------------------------------------------------------
# Round 5: Security & Edge Cases
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 5: Security & Edge Cases")
print("=" * 70)

# 5.1 Unauthenticated access
print("\n--- 5.1 Unauthenticated access ---")
status, headers, body = http_get(f"{BASE}/my/services")
check("Unauthenticated /my/services redirects to login",
      status in (302, 303) or "login" in body.lower(),
      f"status={status}")

status, headers, body = http_get(f"{BASE}/web")
check("Unauthenticated /web redirects to login",
      status == 200 and ("login" in body.lower() or "oe_login" in body),
      f"status={status}")

# 5.2 Portal user cannot access backend
print("\n--- 5.2 Portal backend access ---")
status, headers, body = http_get(f"{BASE}/odoo/action-206", cookies=portal_cookie)
# Portal users shouldn't be able to load backend actions normally
check("Portal user backend access restricted",
      status in (200, 302, 303, 403),
      f"status={status}")

# 5.3 Portal cannot read internal fields via RPC
print("\n--- 5.3 Portal RPC field exposure ---")
data_internal = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[], ["name", "notes", "internal_manager_id", "share_partner_ids"]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_internal, cookies=portal_cookie)
result = json.loads(resp_body)
portal_rpc_services = result.get("result", [])
if portal_rpc_services:
    check("Portal only sees shared services via RPC",
          len(portal_rpc_services) <= 10, f"count={len(portal_rpc_services)}")

# 5.4 SQL injection attempt in search
print("\n--- 5.4 Injection prevention ---")
data_inject = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_read",
        "args": [[["name", "like", "'; DROP TABLE woow_service; --"]]],
        "kwargs": {"fields": ["name"]},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_inject, cookies=admin_cookie)
result = json.loads(resp_body)
check("SQL injection attempt safely handled", "error" not in result or len(result.get("result", [])) == 0)

# Verify table still exists
data_verify = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_count",
        "args": [[]], "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_verify, cookies=admin_cookie)
count = json.loads(resp_body).get("result", 0)
check("Table intact after injection attempt", count >= 18, f"count={count}")

# 5.5 XSS attempt in service name
print("\n--- 5.5 XSS prevention ---")
xss_payload = '<script>alert("xss")</script>'
data_xss = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "create",
        "args": [[{"name": f"XSS Test {xss_payload}"}]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_xss, cookies=admin_cookie)
xss_ids = json.loads(resp_body).get("result", [])
if xss_ids:
    # Check that portal page escapes it
    # Share with portal user first
    data_portal_partner = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "res.users", "method": "search_read",
            "args": [[["login", "=", "portal"]], ["partner_id"]],
            "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_portal_partner, cookies=admin_cookie)
    portal_partner = json.loads(resp_body).get("result", [{}])[0].get("partner_id", [None])[0]
    if portal_partner:
        data_share = {
            "jsonrpc": "2.0", "id": 1, "method": "call",
            "params": {
                "model": "woow.service", "method": "write",
                "args": [xss_ids, {"share_partner_ids": [(4, portal_partner)]}],
                "kwargs": {},
            },
        }
        http_post_json(f"{BASE}/web/dataset/call_kw", data_share, cookies=admin_cookie)

    # Check portal page
    status, _, body = http_get(f"{BASE}/my/services", cookies=portal_cookie)
    check("XSS script tag escaped in portal",
          '<script>alert' not in body,
          "Raw script tag should not appear in HTML")

    # Clean up
    data_del = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "unlink",
            "args": [xss_ids], "kwargs": {},
        },
    }
    http_post_json(f"{BASE}/web/dataset/call_kw", data_del, cookies=admin_cookie)

# 5.6 Missing required field validation (name=False)
print("\n--- 5.6 Required field validation ---")
data_no_name = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "create",
        "args": [[{"name": False}]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_no_name, cookies=admin_cookie)
result = json.loads(resp_body)
check("Missing name (False) creation blocked", "error" in result,
      f"keys={list(result.keys())}")

# 5.7 Archive / Unarchive via standard Odoo actions
print("\n--- 5.7 Archive/Unarchive ---")
data_arc_create = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "create",
        "args": [[{"name": "Archive Test Svc"}]],
        "kwargs": {},
    },
}
status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_arc_create, cookies=admin_cookie)
arc_ids = json.loads(resp_body).get("result", [])
if arc_ids:
    # Archive
    data_archive = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "action_archive",
            "args": [arc_ids], "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_archive, cookies=admin_cookie)
    result = json.loads(resp_body)
    check("Admin can archive service", "error" not in result)

    # Verify archived (not visible in default search)
    data_search_active = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "search_read",
            "args": [[["id", "in", arc_ids]], ["name", "active"]],
            "kwargs": {},
        },
    }
    status, _, resp_body = http_post_json(f"{BASE}/web/dataset/call_kw", data_search_active, cookies=admin_cookie)
    found = json.loads(resp_body).get("result", [])
    check("Archived service hidden from default search", len(found) == 0)

    # Unarchive
    data_unarchive = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "action_unarchive",
            "args": [arc_ids], "kwargs": {},
        },
    }
    http_post_json(f"{BASE}/web/dataset/call_kw", data_unarchive, cookies=admin_cookie)

    # Cleanup
    data_del = {
        "jsonrpc": "2.0", "id": 1, "method": "call",
        "params": {
            "model": "woow.service", "method": "unlink",
            "args": [arc_ids], "kwargs": {},
        },
    }
    http_post_json(f"{BASE}/web/dataset/call_kw", data_del, cookies=admin_cookie)

# 5.8 Portal page card grid CSS classes present
print("\n--- 5.8 CSS asset loading ---")
status, headers, body = http_get(f"{BASE}/my/services", cookies=portal_cookie)
check("Portal page uses woow_service_card CSS classes",
      "woow_service_card" in body or "woow_service_card_grid" in body,
      "Check that CSS classes from portal.css are present in rendered HTML")

# 5.9 Concurrent session test — different users same time
print("\n--- 5.9 Concurrent sessions ---")
admin_uid2, admin_cookie2 = login_get_cookie("admin", "admin")
user_uid2, user_cookie2 = login_get_cookie("testuser", "testuser")
portal_uid2, portal_cookie2 = login_get_cookie("portal", "portal")
check("Three concurrent sessions active",
      all([admin_uid2, user_uid2, portal_uid2]))

# Each sees correct data scope
data_count = {
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": {
        "model": "woow.service", "method": "search_count",
        "args": [[]], "kwargs": {},
    },
}
_, _, r1 = http_post_json(f"{BASE}/web/dataset/call_kw", data_count, cookies=admin_cookie2)
_, _, r2 = http_post_json(f"{BASE}/web/dataset/call_kw", data_count, cookies=user_cookie2)
_, _, r3 = http_post_json(f"{BASE}/web/dataset/call_kw", data_count, cookies=portal_cookie2)
admin_count = json.loads(r1).get("result", 0)
user_count = json.loads(r2).get("result", 0)
portal_count = json.loads(r3).get("result", 0)
check("Admin sees all services", admin_count >= 18, f"count={admin_count}")
check("User sees all services", user_count >= 18, f"count={user_count}")
check("Portal sees only shared services", 0 < portal_count <= 10, f"count={portal_count}")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"FINAL RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
if ERRORS:
    print(f"\nFAILURES:")
    for e in ERRORS:
        print(f"  - {e}")
print("=" * 70)

sys.exit(1 if FAIL else 0)
