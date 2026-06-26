#!/usr/bin/env python3
"""E2E conversation test — runs a full dialogue with the agent and prints transcript."""

import sys
import re
import requests

BASE = "http://localhost:8000/api/v1"
EMAIL = "test@test.com"
PASSWORD = "test"
PRODUCT_ID_PATTERN = re.compile(r"\b[a-z]*id[=:]\s*\d+", re.IGNORECASE)
ISSUES = []


def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


def chat(token, message, cid=None):
    payload = {"message": message, "conversation_id": cid}
    r = requests.post(f"{BASE}/chat", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Chat failed: {r.text}"
    return r.json()


def clear_cart_api(token):
    r = requests.delete(f"{BASE}/cart/clear", headers={"Authorization": f"Bearer {token}"})
    return r.status_code in (200, 204)


def track(msg, text, prods, expect_any=None, id_free=False, expect_cart_item=None, expect_empty=False):
    local = []
    if expect_any:
        txt_clean = text.lower().replace("-", " ")
        if not any(kw.lower().replace("-", " ") in txt_clean for kw in expect_any):
            local.append(f"NONE of {expect_any} in: {text[:150]}")
    if id_free and PRODUCT_ID_PATTERN.search(text):
        local.append(f"Leaked raw ID in: {text[:150]}")
    if expect_cart_item and prods:
        titles = [p["title"].lower() for p in prods]
        if not any(expect_cart_item.lower() in t for t in titles):
            local.append(f"Expected cart item '{expect_cart_item}' not in product cards: {[p['title'] for p in prods]}")
    if expect_empty and text:
        if "empty" not in text.lower():
            local.append(f"Expected 'empty' in: {text[:150]}")
    if local:
        for l in local:
            print(f"  *** {l}")
        ISSUES.append(f"[{msg}]: {' | '.join(local)}")


def say(token, cid, msg, **kw):
    print(f"\n  >>> {msg}")
    resp = chat(token, msg, cid)
    cid = resp["conversation_id"]
    txt = resp.get("response", "(empty)")
    prods = resp.get("products", [])
    print(f"  <<< {txt}")
    if prods:
        for p in prods:
            extra = ""
            if "cart_qty" in p:
                extra = f" [qty={p['cart_qty']}, unit=${p.get('cart_unit_price','?')}, subtotal=${p.get('cart_subtotal','?')}]"
            print(f"       card: {p['title']} (${p.get('price','?')}){extra}")
    track(msg, txt, prods, **kw)
    return resp, cid, prods


def main():
    token = login()
    clear_cart_api(token)

    cid = None
    prods = []

    # ── Phase 1: Search & Sort ────────────────────────────

    say(token, cid, "watches", expect_any=["found"], id_free=True)
    say(token, cid, "only which are in stock",
        expect_any=["found", "in stock", "stock", "available", "availability"], id_free=True)
    say(token, cid, "which one is out of stock",
        expect_any=["out of stock", "found", "information", "referring", "stock"], id_free=True)
    say(token, cid, "which one is cheapest",
        expect_any=["cheapest", "cheap", "least expensive", "lowest price", "looking for", "watch"], id_free=True)
    say(token, cid, "which one is highest rated", expect_any=["highest rated", "highest rating", "looking for", "looking to", "rating"], id_free=True)
    say(token, cid, "which one is lowest rated", expect_any=["lowest rated", "lowest rating", "looking for"], id_free=True)

    # Sort + stock combined
    say(token, cid, "least rated watches in stock",
        expect_any=["least rated", "least-rated", "lowest rated", "lowest-rated", "lowest rating", "found", "result"], id_free=True)
    say(token, cid, "most expensive watches out of stock",
        expect_any=["most expensive", "out of stock"], id_free=True)

    # Categories
    say(token, cid, "show me categories", expect_any=["categor"], id_free=True)

    # ── Phase 2: Product Details & Cart ────────────────────

    say(token, cid, "tell me about the brown leather belt watch", id_free=True)

    # Add to cart — verify the RIGHT product was added
    resp, cid, prods = say(token, cid, "add the brown leather belt watch to my cart",
                           expect_any=["added", "cart has", "item"], id_free=True,
                           expect_cart_item="brown leather belt watch")

    # Cart with enrichment
    resp, cid, prods = say(token, cid, "show me cart",
                           expect_any=["total", "item"], id_free=True,
                           expect_cart_item="brown leather belt watch")

    # Cart qty check
    if prods:
        if not all("cart_qty" in p for p in prods):
            ISSUES.append("[show me cart]: Some product cards missing cart_qty field")

    # Add more
    say(token, cid, "add 2 more brown leather belt watch to my cart",
        expect_any=["added", "updated", "total", "cart has", "item"], id_free=True,
        expect_cart_item="brown leather belt watch")

    # Cart after update
    resp, cid, prods = say(token, cid, "show me cart",
                           expect_any=["total", "item"], id_free=True,
                           expect_cart_item="brown leather belt watch")
    if prods:
        if not all("cart_qty" in p for p in prods):
            ISSUES.append("[show me cart (2)]: Some product cards missing cart_qty field")
        # Verify quantity is > 1 now
        for p in prods:
            if "brown leather" in p["title"].lower():
                if p.get("cart_qty", 0) <= 1:
                    ISSUES.append(f"[show me cart (2)]: Expected qty>1 for belt watch, got {p.get('cart_qty')}")

    # Update quantity
    say(token, cid, "change the brown leather belt watch quantity to 5",
        expect_any=["updated", "changed", "set", "5", "quantity", "cart has", "total"], id_free=True,
        expect_cart_item="brown leather belt watch")

    # Remove from cart
    say(token, cid, "remove the brown leather belt watch from my cart",
        expect_any=["removed", "removing", "cart has", "item"], id_free=True)

    # Verify removed — belt watch should NOT be in cart (other items may exist)
    resp, cid, prods = say(token, cid, "show me cart", id_free=True)
    if prods:
        titles = [p["title"].lower() for p in prods]
        if any("brown leather" in t for t in titles):
            ISSUES.append("[show me cart after remove]: Brown leather belt watch still in cart")

    # Clear
    say(token, cid, "clear my cart", expect_any=["cleared", "emptied", "empty", "cleared"], id_free=True)

    # Verify empty again
    say(token, cid, "show me cart", expect_empty=True, id_free=True)

    # ── Phase 3: Edge Cases ────────────────────────────────

    # Fresh search after cart ops
    say(token, cid, "watches", expect_any=["found"], id_free=True)

    # Sort without explicit query — should use prior context
    say(token, cid, "least rated",
        expect_any=["least rated", "least-rated", "lowest rated", "lowest-rated", "lowest rating"], id_free=True)

    # Ambiguous add
    say(token, cid, "add the watch to my cart", id_free=True)

    # ── Summary ───────────────────────────────────────────

    print("\n" + "=" * 60)
    if ISSUES:
        print(f"\n{len(ISSUES)} ISSUE(S) FOUND:")
        for i in ISSUES:
            print(f"  - {i}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
