#!/usr/bin/env python3
"""Emit candidates-ratios.jsonl. Every number here was read off a query against
ecommerce-truth, never off the ecommerce semantic model."""
import json
import pathlib

SOURCE = {"kind": "authored", "from": "ratios-batch", "seed": "2026-08-30"}
VERIFIED = "authored and re-derived against ecommerce-truth, 2026-08-30"

OI = "duckdb.table('data/order_items.parquet')"
INV = "duckdb.table('data/inventory_items.parquet')"
JOIN_INV = (
    f"{OI} extend {{\n"
    f"  join_one: inventory_items is {INV}\n"
    "    on inventory_item_id = inventory_items.id\n"
    "}"
)

cases = []


def add(**kw):
    kw.setdefault("split", "dev")
    kw.setdefault("state", "selected")
    kw.setdefault("source", SOURCE)
    kw.setdefault("goldenRevision", 1)
    kw["golden"].setdefault("status", "provisional")
    kw["golden"].setdefault("verifiedBy", VERIFIED)
    cases.append(kw)


# ---------------------------------------------------------------- 1
add(
    qid="ecom_avg_selling_price_per_item",
    question="On average, how much do we get for each item we sell?",
    tags=["ratio", "average", "symmetric-aggregate", "weighted-vs-unweighted", "grain"],
    requiresConcepts=["revenue per unit sold", "units vs SKUs"],
    golden={
        "kind": "scalar",
        "value": {
            "avg_selling_price_per_item": 46.3668,
            "total_sales": 12566292.88,
            "items_sold": 271019,
            "currency": "usd",
            "round": 4,
        },
        "canonicalQuery": (
            f"run: {OI} -> {{\n"
            "  aggregate:\n"
            "    total_sales is sale_price.sum()\n"
            "    items_sold is count()\n"
            "} -> {\n"
            "  select:\n"
            "    total_sales\n"
            "    items_sold\n"
            "    avg_selling_price_per_item is round(total_sales / items_sold, 4)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 46.3668 — revenue per unit sold, 12566292.88 / 271019 line items. This is a "
            "volume-weighted average and it is the only reading of 'how much do we get for each item "
            "we sell'.\n"
            "STRUCTURAL (accept: false): 56.4849 — the unweighted mean list price over the 18190 "
            "distinct products that have sold at least one unit. Malloy hands this to an agent "
            "silently: in an order_items context `inventory_items.product.retail_price.avg()` is a "
            "symmetric aggregate, so it de-duplicates to distinct products instead of averaging over "
            "the 271019 rows. The query reads like an average selling price and is an average of "
            "catalogue prices per SKU, giving a $500 coat that sold twice the same weight as a $10 "
            "tee that sold 900 times — 21.8% high. Any answer near 56.48 is this bug.\n"
            "DEFINITIONAL (accept: true): 59.2202 — mean retail_price over all 29120 catalogue "
            "products. Answers 'a product we list', not 'we sell'; 10930 catalogue products have "
            "never sold a unit.\n"
            "Note for graders: sale_price equals inventory_items.product_retail_price on all 271019 "
            "lines (max absolute difference 0.0), so realised-vs-list is NOT the fork here. Grain is. "
            "An answer that gets 46.3668 by averaging product_retail_price on inventory_items (1:1 "
            "with order lines, so no dedup) is correct."
        ),
        "mustState": ["The average is per unit sold, not per distinct product."],
        "mustNotUse": ["an average of per-SKU prices", "products.retail_price.avg() through the product join"],
        "alternates": [
            {
                "assumption": "unweighted mean list price across the 18190 distinct SKUs that have sold (what a symmetric aggregate through the product join returns)",
                "value": {"avg_selling_price_per_item": 56.4849},
                "accept": False,
            },
            {
                "assumption": "average list price of a catalogue product, including the 10930 that never sold",
                "value": {"avg_selling_price_per_item": 59.2202},
                "accept": True,
                "lever": "entities",
            },
        ],
        "clarifyOk": False,
    },
)

# ---------------------------------------------------------------- 2
add(
    qid="ecom_gross_margin_pct",
    question="What's our gross margin percentage?",
    tags=["ratio", "margin", "symmetric-aggregate", "cost-source"],
    requiresConcepts=["gross margin percentage", "cost of goods"],
    golden={
        "kind": "scalar",
        "value": {
            "gross_margin_pct": 0.52235,
            "total_sales": 12566292.88,
            "total_cost": 6002288.38,
            "round": 6,
        },
        "canonicalQuery": (
            f"run: {JOIN_INV} -> {{\n"
            "  aggregate:\n"
            "    total_sales is sale_price.sum()\n"
            "    total_cost is inventory_items.cost.sum()\n"
            "} -> {\n"
            "  select:\n"
            "    total_sales\n"
            "    total_cost\n"
            "    gross_margin_pct is round((total_sales - total_cost) / total_sales, 6)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 0.52235 (52.24%) — (12566292.88 - 6002288.38) / 12566292.88, the ratio recomputed "
            "over the whole population. Cost must come from inventory_items.cost, which is what the "
            "model's own total_gross_margin measure uses.\n"
            "STRUCTURAL (accept: false): 0.961222 (96.12%) — reached by taking cost from the product "
            "catalogue, i.e. `inventory_items.product.cost.sum()`, which returns 487294.47 instead of "
            "6002288.38. The per-row values are IDENTICAL (inventory_items.cost equals product.cost on "
            "all 271019 lines, max absolute difference 0.0), so this is not a cost-definition "
            "disagreement: Malloy's symmetric aggregate sums catalogue cost once per distinct product "
            "(18190 of them), not once per unit sold. A 96% gross margin on apparel should be "
            "self-evidently wrong, which is what makes this a good test. Any answer above ~0.9 is "
            "this bug.\n"
            "STRUCTURAL (accept: false): 0.523223 — the unweighted mean of the per-line margin "
            "percentage. Wrong method (average of ratios), and numerically almost indistinguishable "
            "from the right answer because per-item margin is near-constant in this data, so grade on "
            "the stated method when it is visible, not on the number.\n"
            "DEFINITIONAL (accept: true): 0.522368 on Complete lines only. Defensible; the model "
            "documents no status filter on total_gross_margin.\n"
            "Must not be presented as net profit — there is no operating expense in this dataset."
        ),
        "mustState": ["Gross margin, not net profit; there is no opex in this data."],
        "mustNotUse": ["product.cost summed through the order_items join"],
        "alternates": [
            {
                "assumption": "cost summed from the product catalogue through the order_items join (symmetric aggregate de-duplicates to 18190 products)",
                "value": {"gross_margin_pct": 0.961222},
                "accept": False,
            },
            {
                "assumption": "unweighted mean of the per-line-item margin percentage",
                "value": {"gross_margin_pct": 0.523223},
                "accept": False,
            },
            {
                "assumption": "Complete-status lines only",
                "value": {"gross_margin_pct": 0.522368},
                "accept": True,
                "lever": "field_doc",
            },
        ],
        "clarifyOk": False,
    },
)

# ---------------------------------------------------------------- 3
add(
    qid="ecom_avg_cost_per_item_sold",
    question="What does the average item we sell cost us?",
    tags=["average", "symmetric-aggregate", "cost-source", "grain"],
    requiresConcepts=["cost of goods per unit"],
    golden={
        "kind": "scalar",
        "value": {
            "avg_cost_per_item_sold": 22.1471,
            "total_cost": 6002288.38,
            "items_sold": 271019,
            "currency": "usd",
            "round": 4,
        },
        "canonicalQuery": (
            f"run: {JOIN_INV} -> {{\n"
            "  aggregate:\n"
            "    total_cost is inventory_items.cost.sum()\n"
            "    items_sold is count()\n"
            "} -> {\n"
            "  select:\n"
            "    total_cost\n"
            "    items_sold\n"
            "    avg_cost_per_item_sold is round(total_cost / items_sold, 4)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 22.1471 — 6002288.38 of inventory cost over 271019 units sold. Sits sensibly "
            "against the 46.3668 average selling price (a ~52% margin).\n"
            "STRUCTURAL (accept: false): 1.7980 — the same query with cost taken from the product "
            "catalogue: `inventory_items.product.cost.sum()` returns 487294.47 because Malloy's "
            "symmetric aggregate charges each of the 18190 distinct products once rather than each of "
            "the 271019 units, then dividing by 271019 lines mixes two grains. 12.3x too low, and the "
            "giveaway is that it implies a 96% margin. The trap is live because the two cost fields "
            "carry near-identical docs ('Wholesale cost of this inventory item' vs 'Wholesale cost') "
            "and are equal row-for-row, so nothing warns that only one of them aggregates correctly "
            "from order_items.\n"
            "DEFINITIONAL (accept: true): 26.7891 — the mean catalogue cost of a distinct SKU that has "
            "sold (487294.47 / 18190). A per-SKU rather than per-unit question; 20.9% high because "
            "expensive SKUs sell fewer units. Accept only if the answer says it is per SKU.\n"
            "Also note 28.4818, the mean cost across all 29120 catalogue products including the 10930 "
            "never sold — a different population again."
        ),
        "mustState": ["Per unit sold, and that cost comes from the inventory unit."],
        "mustNotUse": ["product.cost summed through the order_items join"],
        "alternates": [
            {
                "assumption": "catalogue cost summed through the join (de-duplicated to 18190 products) then divided by 271019 lines",
                "value": {"avg_cost_per_item_sold": 1.798},
                "accept": False,
            },
            {
                "assumption": "mean catalogue cost per distinct SKU sold, unweighted by units",
                "value": {"avg_cost_per_item_sold": 26.7891},
                "accept": True,
                "lever": "field_doc",
            },
        ],
        "clarifyOk": False,
    },
)

# ---------------------------------------------------------------- 4
add(
    qid="ecom_avg_spend_per_customer",
    question="On average, how much has each of our customers spent with us?",
    tags=["ratio", "average", "denominator", "grain", "entities"],
    requiresConcepts=["spend per customer", "customers vs users"],
    golden={
        "kind": "scalar",
        "value": {
            "avg_spend_per_customer": 94.239,
            "total_sales": 12566292.88,
            "customers": 133345,
            "currency": "usd",
            "round": 4,
        },
        "canonicalQuery": (
            f"run: {OI} -> {{\n"
            "  aggregate:\n"
            "    total_sales is sale_price.sum()\n"
            "    customers is count(user_id)\n"
            "} -> {\n"
            "  select:\n"
            "    total_sales\n"
            "    customers\n"
            "    avg_spend_per_customer is round(total_sales / customers, 4)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 94.2390 — 12566292.88 over 133345 distinct buyers. Equals the mean of per-customer "
            "lifetime spend, so it is the population ratio and the average-of-groups in agreement.\n"
            "STRUCTURAL (accept: false): 46.3668 — sale_price.avg(), the average LINE ITEM, which the "
            "model offers no measure for and which answers a question nobody asked. Exactly half the "
            "right answer (customers average 2.03 line items each), so it is a 2x error and the "
            "single most likely miss on this question.\n"
            "STRUCTURAL (accept: false): 47.5868 — total sales over 264071 distinct ORDERS. That is "
            "average order value, not spend per customer.\n"
            "DEFINITIONAL (accept: true): 74.7713 — divided by all 168063 registered accounts rather "
            "than the 133345 who bought. Defensible for an ARPU reading; 34718 accounts have never "
            "ordered. The model has two measures both named user_count (order_items.user_count "
            "resolves to buyers, users.user_count to accounts) and neither doc names its population, "
            "so nothing signals that a 34718-row choice is being made."
        ),
        "mustState": ["Which population is the denominator: buyers or all registered accounts."],
        "mustNotUse": ["sale_price.avg() as spend per customer"],
        "alternates": [
            {
                "assumption": "average line item value rather than per customer",
                "value": {"avg_spend_per_customer": 46.3668},
                "accept": False,
            },
            {
                "assumption": "per distinct order rather than per customer",
                "value": {"avg_spend_per_customer": 47.5868},
                "accept": False,
            },
            {
                "assumption": "per registered account, including the 34718 who never ordered",
                "value": {"avg_spend_per_customer": 74.7713},
                "accept": True,
                "lever": "entities",
            },
        ],
        "clarifyOk": True,
    },
)

# ---------------------------------------------------------------- 5
add(
    qid="ecom_customer_return_rate",
    question="What percentage of our customers have ever returned an item?",
    tags=["ratio", "denominator", "grain", "average-of-averages"],
    requiresConcepts=["returns", "customer-level rate"],
    golden={
        "kind": "scalar",
        "value": {
            "customer_return_rate": 0.019806,
            "customers_with_a_return": 2641,
            "customers": 133345,
            "round": 6,
        },
        "canonicalQuery": (
            f"run: {OI} -> {{\n"
            "  group_by: user_id\n"
            "  aggregate: returned_items is count() { where: status = 'Returned' }\n"
            "} -> {\n"
            "  aggregate:\n"
            "    customers is count()\n"
            "    customers_with_a_return is count() { where: returned_items > 0 }\n"
            "} -> {\n"
            "  select:\n"
            "    customers\n"
            "    customers_with_a_return\n"
            "    customer_return_rate is round(customers_with_a_return / customers, 6)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 0.019806 (1.98%) — 2641 of 133345 buyers have at least one Returned line. The "
            "question counts CUSTOMERS, so the unit of both numerator and denominator is a person, "
            "which requires a per-customer roll-up before the ratio.\n"
            "STRUCTURAL (accept: false): 0.009859 (0.99%) — the item return rate, 2672 Returned lines "
            "over 271019 lines. Half the right answer. This is the likely miss because it is the rate "
            "the model composes most naturally and because 'return rate' is a familiar phrase that "
            "hides the change of unit.\n"
            "STRUCTURAL (accept: false): 0.020038 — 2672 returned ITEMS over 133345 CUSTOMERS. "
            "Numerically close to right and structurally incoherent (mismatched grain); 31 customers "
            "have returned more than one item, which is the whole difference between 2672 and 2641.\n"
            "STRUCTURAL (accept: false): 0.009761 — the unweighted mean of each customer's own "
            "returned-share. The model hands the agent exactly this ratio: the frequent_returners view "
            "defines percent_purchases_returned per customer, and averaging that column across "
            "customers is the textbook average-of-averages. It lands near the item rate by coincidence "
            "and is half the true answer.\n"
            "Any answer that reports 2641 or 2672 as a count without a rate is incomplete, not wrong."
        ),
        "mustState": ["The denominator is customers (buyers), not line items."],
        "mustNotUse": ["the item-level return rate as a customer-level rate"],
        "alternates": [
            {
                "assumption": "item-level return rate reported as a customer rate",
                "value": {"customer_return_rate": 0.009859},
                "accept": False,
            },
            {
                "assumption": "returned items divided by customers (mismatched grain)",
                "value": {"customer_return_rate": 0.020038},
                "accept": False,
            },
            {
                "assumption": "unweighted mean of each customer's own returned-item share",
                "value": {"customer_return_rate": 0.009761},
                "accept": False,
            },
        ],
        "clarifyOk": False,
    },
)

# ---------------------------------------------------------------- 6
add(
    qid="ecom_return_share_of_delivered",
    question="Of the items that actually reached the customer, what share came back as returns?",
    tags=["ratio", "denominator", "denominator-excludes-numerator", "returns"],
    requiresConcepts=["returns", "delivered base"],
    golden={
        "kind": "scalar",
        "value": {
            "return_share_of_delivered": 0.010334,
            "returned_items": 2672,
            "delivered_items": 258555,
            "round": 6,
        },
        "canonicalQuery": (
            f"run: {OI} -> {{\n"
            "  aggregate:\n"
            "    returned_items is count() { where: status = 'Returned' }\n"
            "    delivered_items is count() { where: delivered_at is not null }\n"
            "} -> {\n"
            "  select:\n"
            "    returned_items\n"
            "    delivered_items\n"
            "    return_share_of_delivered is round(returned_items / delivered_items, 6)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 0.010334 (1.033%) — 2672 Returned items over 258555 items with a non-null "
            "delivered_at. The base has to CONTAIN the returns: every Returned line is also delivered "
            "(all 2672 have both delivered_at and returned_at set), so delivered = 255883 Complete + "
            "2672 Returned.\n"
            "STRUCTURAL (accept: false): 0.010442 — 2672 over the 255883 Complete lines. This is the "
            "error the case exists to catch: status is a terminal state, so Complete and Returned are "
            "mutually exclusive, and 'delivered' read as status = 'Complete' excludes every single row "
            "in the numerator. The ratio is not a share of anything. The number is only 1% off the "
            "right one, so grade the stated denominator, not the digits.\n"
            "STRUCTURAL (accept: false): 0.009859 — over all 271019 lines. Ignores the base the "
            "question names and folds in 9510 Cancelled and 1227 Processing items that never reached a "
            "customer.\n"
            "DEFINITIONAL (accept: true): 0.010266 — over the 260282 items with a non-null shipped_at. "
            "A defensible reading of 'reached the customer' (it adds the 1727 shipped-not-yet-delivered "
            "items); the field docs say only 'When the order shipped' and 'When the order was "
            "delivered' and never state which marks customer receipt."
        ),
        "mustState": ["The denominator must include the returned items themselves."],
        "mustNotUse": ["status = 'Complete' as the delivered base"],
        "alternates": [
            {
                "assumption": "Complete-status items as the delivered base (excludes all 2672 numerator rows)",
                "value": {"return_share_of_delivered": 0.010442},
                "accept": False,
            },
            {
                "assumption": "all order items, including cancelled and still-processing",
                "value": {"return_share_of_delivered": 0.009859},
                "accept": False,
            },
            {
                "assumption": "shipped items as the base for 'reached the customer'",
                "value": {"return_share_of_delivered": 0.010266},
                "accept": True,
                "lever": "field_doc",
            },
        ],
        "clarifyOk": True,
    },
)

# ---------------------------------------------------------------- 7
add(
    qid="ecom_shipped_item_share",
    question="What percentage of our order items have shipped?",
    tags=["ratio", "numerator", "status-literal", "percentage"],
    requiresConcepts=["shipped items", "order status vs timestamp"],
    golden={
        "kind": "scalar",
        "value": {
            "shipped_share": 0.960383,
            "shipped_items": 260282,
            "total_items": 271019,
            "round": 6,
        },
        "canonicalQuery": (
            f"run: {OI} -> {{\n"
            "  aggregate:\n"
            "    shipped_items is count() { where: shipped_at is not null }\n"
            "    total_items is count()\n"
            "} -> {\n"
            "  select:\n"
            "    shipped_items\n"
            "    total_items\n"
            "    shipped_share is round(shipped_items / total_items, 6)\n"
            "}"
        ),
        "rubric": (
            "RIGHT: 0.960383 (96.04%) — 260282 of 271019 items have a non-null shipped_at: 255883 "
            "Complete + 2672 Returned + 1727 Shipped. 'Has shipped' is a state the item has passed "
            "through, and shipped_at is the only field that records it.\n"
            "STRUCTURAL (accept: false): 0.006372 (0.64%) — filtering status = 'Shipped', which is "
            "1727 items. status is a terminal-state snapshot, so 'Shipped' means shipped and NOT YET "
            "delivered; it excludes the 255883 Complete and 2672 Returned items that obviously "
            "shipped. This is a 151x error and the widest gap in this batch. The trap is live because "
            "the status field doc enumerates the five values without saying they are mutually "
            "exclusive terminal states, and the model ships an orders_by_status view that makes "
            "grouping on the literal look like the intended path.\n"
            "DEFINITIONAL (accept: true): 0.995308 — over the 261509 items that could ship, i.e. "
            "excluding the 9510 Cancelled. A reasonable fulfilment-performance reading; nothing in the "
            "model documents whether cancelled lines belong in a shipping denominator.\n"
            "Note the remaining 10737 unshipped items are 9510 Cancelled plus 1227 Processing."
        ),
        "mustState": ["Shipped is read from shipped_at, not from status = 'Shipped'."],
        "mustNotUse": ["status = 'Shipped' as the set of shipped items"],
        "alternates": [
            {
                "assumption": "status = 'Shipped' literal as the numerator",
                "value": {"shipped_share": 0.006372},
                "accept": False,
            },
            {
                "assumption": "denominator excludes the 9510 cancelled items that could never ship",
                "value": {"shipped_share": 0.995308},
                "accept": True,
                "lever": "field_doc",
            },
        ],
        "clarifyOk": False,
    },
)

# ---------------------------------------------------------------- 8
add(
    qid="ecom_top_margin_pct_categories",
    question="Which five product categories give us the best gross margin percentage?",
    tags=["ratio", "ranking", "symmetric-aggregate", "margin", "weighted-vs-unweighted"],
    requiresConcepts=["margin percentage by category"],
    golden={
        "kind": "rows",
        "value": [
            {"product_category": "Accessories", "margin_pct": 0.628286, "margin_dollars": 746438.18, "total_sales": 1188055.17, "rank": 1},
            {"product_category": "Blazers & Jackets", "margin_pct": 0.620585, "margin_dollars": 329402.47, "total_sales": 530793.84, "rank": 2},
            {"product_category": "Suits & Sport Coats", "margin_pct": 0.598469, "margin_dollars": 283290.06, "total_sales": 473358.17, "rank": 3},
            {"product_category": "Skirts", "margin_pct": 0.596698, "margin_dollars": 139217.58, "total_sales": 233313.45, "rank": 4},
            {"product_category": "Socks & Hosiery", "margin_pct": 0.59514, "margin_dollars": 29161.95, "total_sales": 49000.13, "rank": 5},
        ],
        "canonicalQuery": (
            f"run: {JOIN_INV} -> {{\n"
            "  group_by: product_category is inventory_items.product_category\n"
            "  aggregate:\n"
            "    total_sales is sale_price.sum()\n"
            "    margin_dollars is sale_price.sum() - inventory_items.cost.sum()\n"
            "} -> {\n"
            "  select:\n"
            "    product_category\n"
            "    total_sales\n"
            "    margin_dollars\n"
            "    margin_pct is round(margin_dollars / total_sales, 6)\n"
            "  order_by: margin_pct desc\n"
            "  limit: 5\n"
            "}"
        ),
        "rubric": (
            "RIGHT: Accessories 0.628286, Blazers & Jackets 0.620585, Suits & Sport Coats 0.598469, "
            "Skirts 0.596698, Socks & Hosiery 0.595140 — each category's margin recomputed as its own "
            "margin dollars over its own sales. 5th vs 6th is Socks & Hosiery 0.595140 against Active "
            "0.580912, so there is no tie at the cut.\n"
            "STRUCTURAL (accept: false): ranking by margin DOLLARS gives Jeans (940655.04), "
            "Accessories, Outerwear & Coats, Active, Fashion Hoodies & Sweatshirts. The question asks "
            "for percentage and Jeans is 17th of 26 on it at 0.481376 — it tops the dollar list only "
            "because it is the largest category. Naming Jeans is the likely miss.\n"
            "STRUCTURAL (accept: false): taking cost from the product catalogue "
            "(inventory_items.product.cost) gives Clothing Sets 0.993835, Jumpsuits & Rompers "
            "0.990645, Accessories 0.984532, Pants 0.977702, Jeans 0.977690 — every category above "
            "97%. Malloy's symmetric aggregate charges catalogue cost once per distinct SKU in each "
            "group, so a group's cost falls as its unit volume rises and the ranking inverts: Clothing "
            "Sets is placed FIRST here and is dead last of 26 on the real figure at 0.373765. A "
            "top-five list where every margin exceeds 97% is the tell.\n"
            "DEFINITIONAL (accept: true): with a materiality floor the list becomes Accessories, "
            "Blazers & Jackets, Suits & Sport Coats, Active, Sleep & Lounge — Socks & Hosiery is only "
            "49000.13 of 12566292.88 total sales and Skirts 233313.45. Nothing in the model documents a "
            "minimum-volume rule, so a floor must be stated to be accepted.\n"
            "An answer giving the five names without saying it ranked on percentage is partial."
        ),
        "mustState": ["Ranked on margin percentage, not margin dollars."],
        "mustNotUse": ["margin dollars as the ranking metric", "product.cost through the order_items join"],
        "alternates": [
            {
                "assumption": "ranked by absolute gross margin dollars",
                "value": ["Jeans", "Accessories", "Outerwear & Coats", "Active", "Fashion Hoodies & Sweatshirts"],
                "accept": False,
            },
            {
                "assumption": "cost taken from the product catalogue through the join (symmetric aggregate de-duplicates per SKU)",
                "value": ["Clothing Sets", "Jumpsuits & Rompers", "Accessories", "Pants", "Jeans"],
                "accept": False,
            },
            {
                "assumption": "materiality floor of roughly 250k in category sales applied first",
                "value": ["Accessories", "Blazers & Jackets", "Suits & Sport Coats", "Active", "Sleep & Lounge"],
                "accept": True,
                "lever": "source_doc",
            },
        ],
        "clarifyOk": True,
    },
)


out = pathlib.Path(__file__).parent / "candidates-ratios.jsonl"
out.write_text("".join(json.dumps(c) + "\n" for c in cases))
print(f"wrote {len(cases)} cases to {out.name}")
