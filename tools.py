"""BigQuery tools for the Fashion Shopping Assistant."""

from google.cloud import bigquery

PROJECT_ID = "gcp-ai-sandb-403-408d36c3"
DATASET = "fashion_store"
TABLE = f"{PROJECT_ID}.{DATASET}.product_catalog"
client = bigquery.Client(project=PROJECT_ID)


def _run_query(sql):
    """Execute a BigQuery SQL query and return results as list of dicts."""
    try:
        rows = list(client.query(sql).result())
        if not rows:
            return {"status": "no_results", "data": [], "message": "No products found matching your criteria."}
        data = []
        for row in rows:
            d = dict(row)
            for k, v in d.items():
                if hasattr(v, '__iter__') and not isinstance(v, str):
                    d[k] = list(v)
            data.append(d)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_products(
    category: str = None,
    color: str = None,
    style: str = None,
    occasion: str = None,
    price_tier: str = None,
    max_price: float = None,
    limit: int = 10,
) -> dict:
    """Search the product catalog with optional filters.

    Args:
        category: Product category (dress, top, pants, jacket, accessories)
        color: Primary color (red, blue, black, white, navy, emerald, etc.)
        style: Style type (flowy, fitted, a-line, bodycon, wrap, etc.)
        occasion: Occasion type (evening, cocktail, casual, business, wedding, date_night, brunch, party)
        price_tier: Price tier (budget, mid, premium, luxury)
        max_price: Maximum price filter
        limit: Max number of results to return (default 10)

    Returns:
        dict with status, count, and product data
    """
    conditions = ["in_stock = TRUE"]
    if category:
        conditions.append(f'category = "{category}"')
    if color:
        conditions.append(f'color_primary = "{color}"')
    if style:
        conditions.append(f'style = "{style}"')
    if occasion:
        conditions.append(f'occasion = "{occasion}"')
    if price_tier:
        conditions.append(f'price_tier = "{price_tier}"')
    if max_price:
        conditions.append(f'price <= {max_price}')

    where = " AND ".join(conditions)
    sql = f"""
    SELECT product_id, product_name, category, subcategory, color_primary,
           style, occasion, fabric, price, price_tier, brand,
           description, rating, review_count, size_available, tags
    FROM +"{TABLE}"+f"""
    WHERE {where}
    ORDER BY rating DESC, review_count DESC
    LIMIT {limit}
    """
    return _run_query(sql)


def get_product_details(product_id: str) -> dict:
    """Get full details for a specific product.

    Args:
        product_id: The product ID (e.g., "PROD-0001")

    Returns:
        dict with complete product information
    """
    sql = f"""
    SELECT *
    FROM +"{TABLE}"+f"""
    WHERE product_id = "{product_id}"
    """
    return _run_query(sql)


def get_similar_items(product_id: str, limit: int = 5) -> dict:
    """Find products similar to a given product based on category, style, and occasion.

    Args:
        product_id: The product ID to find similar items for
        limit: Max number of similar items to return

    Returns:
        dict with similar products
    """
    sql = f"""
    WITH source AS (
        SELECT category, style, occasion, color_primary, price, fabric
        FROM +"{TABLE}"+f"""
        WHERE product_id = "{product_id}"
    )
    SELECT p.product_id, p.product_name, p.color_primary, p.style,
           p.occasion, p.fabric, p.price, p.rating, p.review_count,
           p.size_available, p.description
    FROM +"{TABLE}"+f""" p, source s
    WHERE p.product_id != "{product_id}"
      AND p.in_stock = TRUE
      AND p.category = s.category
      AND (p.style = s.style OR p.occasion = s.occasion OR p.fabric = s.fabric)
    ORDER BY
        (CASE WHEN p.style = s.style THEN 1 ELSE 0 END +
         CASE WHEN p.occasion = s.occasion THEN 1 ELSE 0 END +
         CASE WHEN p.fabric = s.fabric THEN 1 ELSE 0 END) DESC,
        p.rating DESC
    LIMIT {limit}
    """
    return _run_query(sql)


def filter_by_attributes(
    category: str = None,
    fabric: str = None,
    season: str = None,
    tag: str = None,
    min_rating: float = None,
    limit: int = 10,
) -> dict:
    """Filter products by specific attributes like fabric, season, or tags.

    Args:
        category: Product category to filter within
        fabric: Fabric type (silk, chiffon, cotton, satin, velvet, etc.)
        season: Season (spring, summer, fall, winter, all_season)
        tag: A specific tag to search for (e.g., "backless", "v_neck", "floor_length")
        min_rating: Minimum rating filter
        limit: Max results

    Returns:
        dict with filtered products
    """
    conditions = ["in_stock = TRUE"]
    if category:
        conditions.append(f'category = "{category}"')
    if fabric:
        conditions.append(f'fabric = "{fabric}"')
    if season:
        conditions.append(f'(season = "{season}" OR season = "all_season")')
    if tag:
        conditions.append(f'"{tag}" IN UNNEST(tags)')
    if min_rating:
        conditions.append(f'rating >= {min_rating}')

    where = " AND ".join(conditions)
    sql = f"""
    SELECT product_id, product_name, category, color_primary, style,
           occasion, fabric, price, rating, review_count, tags,
           size_available, description
    FROM +"{TABLE}"+f"""
    WHERE {where}
    ORDER BY rating DESC
    LIMIT {limit}
    """
    return _run_query(sql)


def get_style_tips(occasion: str, season: str = None) -> dict:
    """Get style recommendations based on occasion and season by analyzing top-rated products.

    Args:
        occasion: The occasion (evening, cocktail, casual, business, wedding, date_night)
        season: Optional season filter

    Returns:
        dict with popular styles, fabrics, and colors for the occasion
    """
    season_filter = ""
    if season:
        season_filter = f'AND (season = "{season}" OR season = "all_season")'

    sql = f"""
    SELECT
        style,
        fabric,
        color_primary,
        COUNT(*) as product_count,
        ROUND(AVG(rating), 1) as avg_rating,
        ROUND(AVG(price), 0) as avg_price
    FROM +"{TABLE}"+f"""
    WHERE occasion = "{occasion}"
      AND in_stock = TRUE
      AND rating >= 4.0
      {season_filter}
    GROUP BY style, fabric, color_primary
    ORDER BY avg_rating DESC, product_count DESC
    LIMIT 10
    """
    return _run_query(sql)


def compare_styles(product_id_1: str, product_id_2: str) -> dict:
    """Compare two products side by side.

    Args:
        product_id_1: First product ID
        product_id_2: Second product ID

    Returns:
        dict with both products for comparison
    """
    sql = f"""
    SELECT product_id, product_name, color_primary, style, occasion,
           fabric, price, rating, review_count, size_available,
           tags, description
    FROM +"{TABLE}"+f"""
    WHERE product_id IN ("{product_id_1}", "{product_id_2}")
    """
    return _run_query(sql)


def suggest_accessories(product_id: str) -> dict:
    """Suggest accessories that pair well with a given product.

    Args:
        product_id: The product ID to find accessories for

    Returns:
        dict with matching accessories
    """
    sql = f"""
    WITH source AS (
        SELECT occasion, color_primary, price_tier
        FROM +"{TABLE}"+f"""
        WHERE product_id = "{product_id}"
    )
    SELECT a.product_id, a.product_name, a.subcategory, a.color_primary,
           a.style, a.price, a.rating, a.description
    FROM +"{TABLE}"+f""" a, source s
    WHERE a.category = "accessories"
      AND a.in_stock = TRUE
      AND (a.color_primary = s.color_primary
           OR a.color_primary IN ("gold", "silver", "black"))
    ORDER BY
        CASE WHEN a.occasion = s.occasion THEN 1 ELSE 0 END DESC,
        a.rating DESC
    LIMIT 5
    """
    return _run_query(sql)


def get_trending(category: str, season: str = None) -> dict:
    """Get trending products based on highest ratings and most reviews.

    Args:
        category: Product category
        season: Optional season filter

    Returns:
        dict with trending products
    """
    season_filter = ""
    if season:
        season_filter = f'AND (season = "{season}" OR season = "all_season")'

    sql = f"""
    SELECT product_id, product_name, color_primary, style, occasion,
           fabric, price, rating, review_count, description
    FROM +"{TABLE}"+f"""
    WHERE category = "{category}"
      AND in_stock = TRUE
      AND rating >= 4.3
      {season_filter}
    ORDER BY review_count DESC, rating DESC
    LIMIT 10
    """
    return _run_query(sql)


def check_stock(product_id: str, size: str = None) -> dict:
    """Check stock availability for a product, optionally for a specific size.

    Args:
        product_id: The product ID to check
        size: Optional specific size to check (XS, S, M, L, XL, XXL)

    Returns:
        dict with stock status and available sizes
    """
    sql = f"""
    SELECT product_id, product_name, in_stock, stock_quantity, size_available
    FROM +"{TABLE}"+f"""
    WHERE product_id = "{product_id}"
    """
    result = _run_query(sql)
    if result["status"] == "success" and size:
        product = result["data"][0]
        sizes = product.get("size_available", [])
        result["size_requested"] = size
        result["size_available"] = size in sizes
    return result


def get_price_range(category: str, occasion: str = None) -> dict:
    """Get the price range and distribution for a category.

    Args:
        category: Product category
        occasion: Optional occasion filter

    Returns:
        dict with min, max, average prices and tier breakdown
    """
    occasion_filter = ""
    if occasion:
        occasion_filter = f'AND occasion = "{occasion}"'

    sql = f"""
    SELECT
        ROUND(MIN(price), 2) as min_price,
        ROUND(MAX(price), 2) as max_price,
        ROUND(AVG(price), 2) as avg_price,
        COUNT(*) as total_products,
        COUNTIF(price_tier = "budget") as budget_count,
        COUNTIF(price_tier = "mid") as mid_count,
        COUNTIF(price_tier = "premium") as premium_count,
        COUNTIF(price_tier = "luxury") as luxury_count
    FROM +"{TABLE}"+f"""
    WHERE category = "{category}"
      AND in_stock = TRUE
      {occasion_filter}
    """
    return _run_query(sql)


def find_deals(category: str = None, max_price: float = None, limit: int = 10) -> dict:
    """Find the best-rated products under a budget.

    Args:
        category: Optional category filter
        max_price: Maximum price
        limit: Max results

    Returns:
        dict with best deals (highest rated at lowest price)
    """
    conditions = ["in_stock = TRUE"]
    if category:
        conditions.append(f'category = "{category}"')
    if max_price:
        conditions.append(f'price <= {max_price}')

    where = " AND ".join(conditions)
    sql = f"""
    SELECT product_id, product_name, category, color_primary, style,
           occasion, price, rating, review_count, description
    FROM +"{TABLE}"+f"""
    WHERE {where}
    ORDER BY rating DESC, price ASC
    LIMIT {limit}
    """
    return _run_query(sql)
