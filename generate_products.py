import json
import random
from datetime import datetime, timedelta

random.seed(42)

CATEGORIES = {
    "dress": {"subcategories": ["evening_dress", "cocktail_dress", "casual_dress", "maxi_dress", "mini_dress"], "styles": ["flowy", "fitted", "a-line", "bodycon", "wrap", "empire_waist", "shift"], "price_range": (45, 350), "names": ["Gown", "Dress", "Frock", "Sheath", "Slip Dress"]},
    "top": {"subcategories": ["blouse", "t_shirt", "crop_top", "tank_top", "sweater"], "styles": ["relaxed", "fitted", "oversized", "cropped", "peplum"], "price_range": (25, 150), "names": ["Blouse", "Top", "Tee", "Sweater", "Cami"]},
    "pants": {"subcategories": ["trousers", "jeans", "wide_leg", "leggings", "culottes"], "styles": ["slim", "wide_leg", "bootcut", "straight", "tapered"], "price_range": (35, 200), "names": ["Trousers", "Pants", "Jeans", "Leggings", "Culottes"]},
    "jacket": {"subcategories": ["blazer", "denim_jacket", "leather_jacket", "cardigan", "coat"], "styles": ["fitted", "oversized", "cropped", "longline", "structured"], "price_range": (55, 400), "names": ["Blazer", "Jacket", "Cardigan", "Coat", "Bomber"]},
    "accessories": {"subcategories": ["handbag", "scarf", "belt", "jewelry", "hat"], "styles": ["statement", "minimal", "classic", "boho", "modern"], "price_range": (15, 250), "names": ["Bag", "Scarf", "Belt", "Necklace", "Hat"]},
}
COLORS = ["red", "blue", "black", "white", "navy", "emerald", "burgundy", "blush", "gold", "silver", "coral", "teal", "ivory", "charcoal", "lavender", "forest_green", "dusty_rose", "champagne", "cobalt", "rust"]
SECONDARY_COLORS = [None, None, None, "gold", "silver", "black", "white", "ivory", "lace"]
OCCASIONS = ["evening", "cocktail", "casual", "business", "wedding", "date_night", "brunch", "party"]
FABRICS = ["silk", "chiffon", "cotton", "polyester", "linen", "velvet", "satin", "jersey", "wool", "cashmere", "denim", "leather", "lace", "tulle"]
SEASONS = ["spring", "summer", "fall", "winter", "all_season"]
BRANDS = ["Elegance Co", "StyleHouse", "Urban Thread", "Luxe Label", "Modern Muse", "Classic Chic", "Bohemian Dreams", "Power Stitch", "Silk Road", "Velvet Edge"]
ALL_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
COLOR_ADJECTIVES = {"red": "Crimson", "blue": "Azure", "black": "Noir", "white": "Pearl", "navy": "Midnight", "emerald": "Emerald", "burgundy": "Bordeaux", "blush": "Blush", "gold": "Golden", "silver": "Sterling", "coral": "Coral", "teal": "Teal", "ivory": "Ivory", "charcoal": "Smoke", "lavender": "Lavender", "forest_green": "Forest", "dusty_rose": "Rose", "champagne": "Champagne", "cobalt": "Cobalt", "rust": "Copper"}
STYLE_ADJECTIVES = {"flowy": "Cascade", "fitted": "Sculpted", "a-line": "Classic", "bodycon": "Contour", "wrap": "Wrapped", "empire_waist": "Empire", "shift": "Modern", "relaxed": "Easy", "oversized": "Luxe", "cropped": "Cropped", "peplum": "Flared", "slim": "Sleek", "wide_leg": "Wide", "bootcut": "Retro", "straight": "Clean", "tapered": "Tapered", "longline": "Long", "structured": "Sharp", "statement": "Bold", "minimal": "Minimal", "classic": "Timeless", "boho": "Free Spirit", "modern": "Edge"}
TAG_OPTIONS = {"dress": ["floor_length", "midi", "mini", "v_neck", "scoop_neck", "halter", "backless", "long_sleeve", "sleeveless", "off_shoulder", "sparkle", "ruched", "pleated", "slit", "tiered", "embroidered"], "top": ["v_neck", "crew_neck", "button_down", "long_sleeve", "short_sleeve", "sleeveless", "lace_trim", "ruffled", "embroidered", "printed"], "pants": ["high_waist", "mid_rise", "low_rise", "pleated", "cuffed", "cropped", "full_length", "pockets", "belt_loops", "stretch"], "jacket": ["double_breasted", "single_breasted", "zip_front", "belted", "padded_shoulders", "lined", "pockets", "hood", "fur_trim"], "accessories": ["adjustable", "one_size", "handmade", "gold_hardware", "silver_hardware", "leather_trim", "chain_strap", "magnetic_closure"]}

products = []
product_id = 1
for category, config in CATEGORIES.items():
    count = 80 if category == "dress" else 55
    for i in range(count):
        color = random.choice(COLORS)
        style = random.choice(config["styles"])
        subcategory = random.choice(config["subcategories"])
        occasion = random.choice(OCCASIONS)
        fabric = random.choice(FABRICS)
        brand = random.choice(BRANDS)
        season = random.choice(SEASONS)
        secondary = random.choice(SECONDARY_COLORS)
        low, high = config["price_range"]
        price = round(random.uniform(low, high), 2)
        if price < 50: price_tier = "budget"
        elif price < 120: price_tier = "mid"
        elif price < 250: price_tier = "premium"
        else: price_tier = "luxury"
        color_adj = COLOR_ADJECTIVES.get(color, color.title())
        style_adj = STYLE_ADJECTIVES.get(style, style.title())
        item_name = random.choice(config["names"])
        product_name = f"{color_adj} {style_adj} {item_name}"
        num_sizes = random.randint(3, 6)
        start = random.randint(0, len(ALL_SIZES) - num_sizes)
        sizes = ALL_SIZES[start:start + num_sizes]
        in_stock = random.random() > 0.1
        stock_qty = random.randint(1, 50) if in_stock else 0
        rating = round(random.uniform(3.5, 5.0), 1)
        reviews = random.randint(10, 500)
        tags = random.sample(TAG_OPTIONS[category], k=random.randint(2, 5))
        description = f"A {style} {item_name.lower()} in {color.replace('_', ' ')} {fabric}. Perfect for {occasion.replace('_', ' ')} occasions. Features a {tags[0].replace('_', ' ')} design" + (f" with {tags[1].replace('_', ' ')} detail" if len(tags) > 1 else "") + "."
        days_ago = random.randint(1, 365)
        created = datetime.now() - timedelta(days=days_ago)
        products.append({"product_id": f"PROD-{product_id:04d}", "product_name": product_name, "category": category, "subcategory": subcategory, "color_primary": color, "color_secondary": secondary, "style": style, "occasion": occasion, "fabric": fabric, "size_available": sizes, "price": price, "price_tier": price_tier, "brand": brand, "description": description, "image_url": f"https://placeholder.fashion/products/PROD-{product_id:04d}.jpg", "rating": rating, "review_count": reviews, "in_stock": in_stock, "stock_quantity": stock_qty, "season": season, "tags": tags, "created_at": created.strftime("%Y-%m-%d %H:%M:%S")})
        product_id += 1

with open("products.json", "w") as f:
    for p in products:
        f.write(json.dumps(p) + "\n")
print(f"Generated {len(products)} products")
