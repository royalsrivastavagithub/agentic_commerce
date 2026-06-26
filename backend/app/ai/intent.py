INTENT_MAP: list[tuple[set[str], str]] = [
    ({"add", "cart", "put", "place"}, "cart"),
    ({"cart", "bag", "basket"}, "cart"),
    ({"cheapest", "least expensive", "lowest price", "cheap"}, "search"),
    ({"most expensive", "priciest", "costliest", "pricey"}, "search"),
    ({"highest rated", "best rated", "top rated", "best reviewed"}, "search"),
    ({"lowest rated", "worst rated", "least rated", "worst reviewed", "poorest rated"}, "search"),
    ({"best discount", "biggest discount", "offer", "deal", "sale", "on sale"}, "search"),
    ({"most reviewed", "most popular", "most bought", "most sold", "popular"}, "search"),
    ({"least reviewed", "least popular", "least bought"}, "search"),
    ({"newest", "new arrivals", "latest", "just in", "new"}, "search"),
    ({"highest stock", "most available", "most stock", "plenty"}, "search"),
    ({"lowest stock", "least available", "least stock", "running out", "almost gone"}, "search"),
    ({"category", "categories", "department", "section"}, "category"),
    ({"detail", "describe", "tell me about", "info", "specs", "specification", "details"}, "info"),
    ({"remove", "delete", "take out", "clear my cart", "empty cart"}, "cart"),
    ({"update", "change quantity", "change to", "set to"}, "cart"),
    ({"search", "find", "show", "look for", "browse", "watches", "laptop", "phone", "shoe"}, "search"),
]

INTENT_TOOLS: dict[str, set[str]] = {
    "search": {"search_products", "get_product_details", "list_categories"},
    "cart": {"add_to_cart", "get_cart_summary", "update_cart_item", "remove_cart_item", "clear_cart", "search_products", "get_product_details"},
    "info": {"get_product_details", "list_categories", "search_products"},
    "category": {"list_categories"},
}


def classify_intent(message: str) -> str:
    """Determine user intent from message text using keyword matching."""
    lower = message.lower()

    if any(word in lower for word in {"add", "cart", "put in", "remove", "update", "clear my cart", "empty cart", "my cart", "shopping cart", "bag", "basket"}):
        return "cart"

    for keywords, intent in INTENT_MAP:
        for kw in keywords:
            if kw in lower:
                return intent

    return "search"


def filter_tools(tools: list, intent: str) -> list:
    """Return only tools relevant to the detected intent."""
    allowed = INTENT_TOOLS.get(intent)
    if allowed is None:
        return tools
    return [t for t in tools if t.name in allowed]
