import json
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Product


API_URL = "https://dummyjson.com/products?limit=0"
USD_TO_UZS = Decimal("13000")
PRODUCTS_PER_SUBCATEGORY = 10

CATEGORY_COLORS = {
    "Elektronika": ["#111827", "#2563eb", "#94a3b8"],
    "Sport": ["#14532d", "#1d4ed8", "#f97316"],
    "Erkaklar Kiyimi": ["#1f2937", "#d6d3d1", "#78716c"],
    "Ayollar Modasi": ["#9d174d", "#fb7185", "#f5d0fe"],
    "Soat va Aksessuarlar": ["#111827", "#d4af37", "#cbd5e1"],
    "Go'zallik": ["#ec4899", "#f9a8d4", "#fdf2f8"],
    "Uy Interyeri": ["#8b5e3c", "#d6d3d1", "#475569"],
    "Oshxona": ["#b91c1c", "#f59e0b", "#1f2937"],
    "Oziq-ovqat": ["#15803d", "#eab308", "#f97316"],
    "Transport": ["#111827", "#dc2626", "#64748b"],
}

SHOE_SIZES = ["39", "40", "41", "42", "43", "44"]
CLOTHING_SIZES = ["S", "M", "L", "XL"]

VARIANT_SETS = {
    "electronics": [
        {"label": "128GB Midnight", "multiplier": Decimal("1.00"), "feature": "128GB xotira", "stock_delta": 3},
        {"label": "128GB Silver", "multiplier": Decimal("1.01"), "feature": "Kumush rang", "stock_delta": 2},
        {"label": "256GB Midnight", "multiplier": Decimal("1.08"), "feature": "256GB xotira", "stock_delta": 1},
        {"label": "256GB Blue", "multiplier": Decimal("1.09"), "feature": "Ko'k rang", "stock_delta": 0},
        {"label": "512GB Pro", "multiplier": Decimal("1.16"), "feature": "Pro daraja konfiguratsiya", "stock_delta": -1},
        {"label": "512GB Graphite", "multiplier": Decimal("1.17"), "feature": "Graphite korpus", "stock_delta": -1},
        {"label": "Creator Edition", "multiplier": Decimal("1.13"), "feature": "Kontent creator uchun mos", "stock_delta": 2},
        {"label": "Business Edition", "multiplier": Decimal("1.12"), "feature": "Biznes ishlar uchun optimallashtirilgan", "stock_delta": 1},
        {"label": "Travel Edition", "multiplier": Decimal("1.06"), "feature": "Safar uchun qulay variant", "stock_delta": 3},
        {"label": "Premium Bundle", "multiplier": Decimal("1.20"), "feature": "Qo'shimcha premium aksessuarlar bilan", "stock_delta": -2},
    ],
    "audio": [
        {"label": "Matte Black", "multiplier": Decimal("1.00"), "feature": "Matte Black finish", "stock_delta": 3},
        {"label": "Pearl White", "multiplier": Decimal("1.01"), "feature": "Pearl White finish", "stock_delta": 2},
        {"label": "Sport Edition", "multiplier": Decimal("1.05"), "feature": "Sport uchun mustahkam dizayn", "stock_delta": 2},
        {"label": "Noise Cancel", "multiplier": Decimal("1.10"), "feature": "Faol shovqin bloklash", "stock_delta": 0},
        {"label": "Wireless Pro", "multiplier": Decimal("1.12"), "feature": "Yuqori sinf wireless ulanish", "stock_delta": -1},
        {"label": "Studio Edition", "multiplier": Decimal("1.15"), "feature": "Studio darajadagi audio", "stock_delta": -1},
        {"label": "Compact Travel", "multiplier": Decimal("1.04"), "feature": "Ixcham sayohat formati", "stock_delta": 3},
        {"label": "Long Battery", "multiplier": Decimal("1.08"), "feature": "Uzoq quvvat saqlash", "stock_delta": 1},
        {"label": "Smart Home", "multiplier": Decimal("1.09"), "feature": "Smart uy integratsiyasi", "stock_delta": 1},
        {"label": "Premium Pack", "multiplier": Decimal("1.18"), "feature": "Premium komplektatsiya", "stock_delta": -2},
    ],
    "sport": [
        {"label": "Training Edition", "multiplier": Decimal("1.00"), "feature": "Mashg'ulot uchun mos", "stock_delta": 4},
        {"label": "Club Edition", "multiplier": Decimal("1.03"), "feature": "Klub o'yinlari uchun", "stock_delta": 3},
        {"label": "Match Edition", "multiplier": Decimal("1.06"), "feature": "Rasmiy uchrashuvlar uchun", "stock_delta": 2},
        {"label": "Pro Grip", "multiplier": Decimal("1.07"), "feature": "Kuchli grip texnologiyasi", "stock_delta": 1},
        {"label": "Team Pack", "multiplier": Decimal("1.09"), "feature": "Jamoaviy foydalanish uchun", "stock_delta": 0},
        {"label": "Outdoor Series", "multiplier": Decimal("1.05"), "feature": "Outdoor ishlatish uchun", "stock_delta": 2},
        {"label": "Indoor Series", "multiplier": Decimal("1.04"), "feature": "Indoor ishlatish uchun", "stock_delta": 2},
        {"label": "Performance Fit", "multiplier": Decimal("1.11"), "feature": "Performance darajadagi tuzilma", "stock_delta": 1},
        {"label": "Elite Control", "multiplier": Decimal("1.13"), "feature": "Aniq nazorat hissi", "stock_delta": 0},
        {"label": "Premium Kit", "multiplier": Decimal("1.16"), "feature": "Premium sport to'plami", "stock_delta": -1},
    ],
    "fashion": [
        {"label": "Classic Fit", "multiplier": Decimal("1.00"), "feature": "Classic fit", "stock_delta": 4},
        {"label": "Regular Fit", "multiplier": Decimal("1.01"), "feature": "Regular fit", "stock_delta": 4},
        {"label": "Slim Fit", "multiplier": Decimal("1.03"), "feature": "Slim fit siluet", "stock_delta": 3},
        {"label": "Oversize", "multiplier": Decimal("1.04"), "feature": "Oversize fason", "stock_delta": 2},
        {"label": "Weekend Edit", "multiplier": Decimal("1.05"), "feature": "Dam olish kunlari uchun", "stock_delta": 2},
        {"label": "Office Edit", "multiplier": Decimal("1.06"), "feature": "Ofisga mos talqin", "stock_delta": 1},
        {"label": "Premium Cotton", "multiplier": Decimal("1.09"), "feature": "Premium cotton material", "stock_delta": 1},
        {"label": "Soft Touch", "multiplier": Decimal("1.08"), "feature": "Soft touch mato", "stock_delta": 2},
        {"label": "Street Edition", "multiplier": Decimal("1.10"), "feature": "Streetwear uslubida", "stock_delta": 1},
        {"label": "Signature Drop", "multiplier": Decimal("1.13"), "feature": "Signature capsule", "stock_delta": 0},
    ],
    "accessory": [
        {"label": "Classic Strap", "multiplier": Decimal("1.00"), "feature": "Classic strap", "stock_delta": 3},
        {"label": "Leather Edition", "multiplier": Decimal("1.05"), "feature": "Charm detallar", "stock_delta": 2},
        {"label": "Steel Finish", "multiplier": Decimal("1.07"), "feature": "Po'lat finish", "stock_delta": 1},
        {"label": "Rose Gold", "multiplier": Decimal("1.08"), "feature": "Rose Gold rang", "stock_delta": 1},
        {"label": "Minimal Dial", "multiplier": Decimal("1.06"), "feature": "Minimal dizayn", "stock_delta": 2},
        {"label": "Luxury Line", "multiplier": Decimal("1.12"), "feature": "Luxury line", "stock_delta": 0},
        {"label": "Weekend Style", "multiplier": Decimal("1.04"), "feature": "Weekend style", "stock_delta": 2},
        {"label": "Formal Look", "multiplier": Decimal("1.09"), "feature": "Formal ko'rinish", "stock_delta": 1},
        {"label": "Gift Pack", "multiplier": Decimal("1.10"), "feature": "Sovg'a uchun tayyor pack", "stock_delta": 1},
        {"label": "Collector Edition", "multiplier": Decimal("1.15"), "feature": "Collector edition", "stock_delta": 0},
    ],
    "beauty": [
        {"label": "Daily Care", "multiplier": Decimal("1.00"), "feature": "Har kunlik foydalanish uchun", "stock_delta": 4},
        {"label": "Travel Size", "multiplier": Decimal("0.95"), "feature": "Travel size format", "stock_delta": 5},
        {"label": "Soft Glow", "multiplier": Decimal("1.03"), "feature": "Soft glow natija", "stock_delta": 3},
        {"label": "Hydra Boost", "multiplier": Decimal("1.06"), "feature": "Namlikni ushlab turadi", "stock_delta": 2},
        {"label": "Night Routine", "multiplier": Decimal("1.07"), "feature": "Tungi parvarish uchun", "stock_delta": 2},
        {"label": "Morning Fresh", "multiplier": Decimal("1.05"), "feature": "Ertalabgi routine uchun", "stock_delta": 3},
        {"label": "Sensitive Skin", "multiplier": Decimal("1.08"), "feature": "Nozik teri uchun", "stock_delta": 1},
        {"label": "Salon Finish", "multiplier": Decimal("1.10"), "feature": "Salon darajasidagi finish", "stock_delta": 1},
        {"label": "Premium Care", "multiplier": Decimal("1.12"), "feature": "Premium care formulasi", "stock_delta": 0},
        {"label": "Gift Set", "multiplier": Decimal("1.15"), "feature": "Sovg'a set ko'rinishida", "stock_delta": 0},
    ],
    "home": [
        {"label": "Oak Finish", "multiplier": Decimal("1.00"), "feature": "Oak finish", "stock_delta": 2},
        {"label": "Walnut Finish", "multiplier": Decimal("1.04"), "feature": "Walnut finish", "stock_delta": 2},
        {"label": "Minimal Style", "multiplier": Decimal("1.03"), "feature": "Minimal interyer uchun", "stock_delta": 3},
        {"label": "Modern Loft", "multiplier": Decimal("1.07"), "feature": "Modern loft uslubi", "stock_delta": 1},
        {"label": "Scandi Look", "multiplier": Decimal("1.06"), "feature": "Scandinavian dizayn", "stock_delta": 2},
        {"label": "Family Edition", "multiplier": Decimal("1.08"), "feature": "Oilaviy foydalanuv uchun", "stock_delta": 1},
        {"label": "Compact Room", "multiplier": Decimal("1.02"), "feature": "Kichik xona uchun mos", "stock_delta": 3},
        {"label": "Premium Decor", "multiplier": Decimal("1.10"), "feature": "Premium dekor aksenti", "stock_delta": 1},
        {"label": "Art Line", "multiplier": Decimal("1.11"), "feature": "Art line dizayni", "stock_delta": 0},
        {"label": "Signature Home", "multiplier": Decimal("1.14"), "feature": "Signature home collection", "stock_delta": 0},
    ],
    "kitchen": [
        {"label": "Chef Edition", "multiplier": Decimal("1.00"), "feature": "Chef edition", "stock_delta": 4},
        {"label": "Home Edition", "multiplier": Decimal("1.01"), "feature": "Uy uchun qulay variant", "stock_delta": 4},
        {"label": "Steel Finish", "multiplier": Decimal("1.04"), "feature": "Steel finish", "stock_delta": 3},
        {"label": "Compact Set", "multiplier": Decimal("1.03"), "feature": "Ixcham set", "stock_delta": 3},
        {"label": "Family Pack", "multiplier": Decimal("1.06"), "feature": "Oilaviy pack", "stock_delta": 2},
        {"label": "Quick Cook", "multiplier": Decimal("1.05"), "feature": "Tez pishirish uchun", "stock_delta": 2},
        {"label": "Daily Use", "multiplier": Decimal("1.02"), "feature": "Har kunlik ishlatish uchun", "stock_delta": 3},
        {"label": "Premium Line", "multiplier": Decimal("1.09"), "feature": "Premium line", "stock_delta": 1},
        {"label": "Gift Kitchen", "multiplier": Decimal("1.08"), "feature": "Kitchen gift variant", "stock_delta": 2},
        {"label": "Pro Kit", "multiplier": Decimal("1.12"), "feature": "Professional kit", "stock_delta": 1},
    ],
    "grocery": [
        {"label": "Fresh Pack 500g", "multiplier": Decimal("1.00"), "feature": "500g qadoq", "stock_delta": 8},
        {"label": "Fresh Pack 1kg", "multiplier": Decimal("1.05"), "feature": "1kg qadoq", "stock_delta": 7},
        {"label": "Family Pack 2kg", "multiplier": Decimal("1.12"), "feature": "2kg oilaviy qadoq", "stock_delta": 6},
        {"label": "Market Select", "multiplier": Decimal("1.03"), "feature": "Saralangan mahsulot", "stock_delta": 7},
        {"label": "Daily Choice", "multiplier": Decimal("1.02"), "feature": "Kundalik tanlov", "stock_delta": 8},
        {"label": "Premium Choice", "multiplier": Decimal("1.08"), "feature": "Premium saralash", "stock_delta": 5},
        {"label": "Chef Choice", "multiplier": Decimal("1.07"), "feature": "Oshpaz tanlovi", "stock_delta": 6},
        {"label": "Healthy Pick", "multiplier": Decimal("1.04"), "feature": "Sog'lom turmush uchun", "stock_delta": 7},
        {"label": "Value Pack", "multiplier": Decimal("1.09"), "feature": "Narx va hajm balansi", "stock_delta": 6},
        {"label": "Signature Basket", "multiplier": Decimal("1.14"), "feature": "Signature basket", "stock_delta": 5},
    ],
    "transport": [
        {"label": "Standard Trim", "multiplier": Decimal("1.00"), "feature": "Standard trim", "stock_delta": 1},
        {"label": "City Edition", "multiplier": Decimal("1.04"), "feature": "Shahar uchun qulay trim", "stock_delta": 1},
        {"label": "Touring Pack", "multiplier": Decimal("1.08"), "feature": "Touring pack", "stock_delta": 0},
        {"label": "Comfort Line", "multiplier": Decimal("1.10"), "feature": "Comfort line", "stock_delta": 0},
        {"label": "Sport Line", "multiplier": Decimal("1.12"), "feature": "Sport suspension ruhida", "stock_delta": 0},
        {"label": "Premium Cabin", "multiplier": Decimal("1.14"), "feature": "Premium salon", "stock_delta": -1},
        {"label": "Tech Package", "multiplier": Decimal("1.16"), "feature": "Texnologik paket bilan", "stock_delta": -1},
        {"label": "Black Edition", "multiplier": Decimal("1.13"), "feature": "Black Edition ko'rinishida", "stock_delta": 0},
        {"label": "Adventure Setup", "multiplier": Decimal("1.11"), "feature": "Adventure setup", "stock_delta": 0},
        {"label": "Signature Drive", "multiplier": Decimal("1.18"), "feature": "Signature drive darajasi", "stock_delta": -1},
    ],
}

CATEGORY_CONFIGS = [
    {
        "name": "Elektronika",
        "emoji": "💻",
        "description": "Telefon, noutbuk va gadjetlar katalogi.",
        "sort_order": 1,
        "subcategories": [
            {"name": "Telefonlar", "sources": ["smartphones"], "variant_set": "electronics"},
            {"name": "Noutbuklar", "sources": ["laptops"], "variant_set": "electronics"},
            {"name": "Planshetlar", "sources": ["tablets"], "variant_set": "electronics"},
            {"name": "Quloqchinlar", "sources": ["mobile-accessories"], "include_keywords": ["airpod", "headphone", "homepod"], "variant_set": "audio"},
            {"name": "Smart Gadjetlar", "sources": ["mobile-accessories"], "include_keywords": ["echo", "charger", "wireless", "smart", "power"], "variant_set": "audio"},
        ],
    },
    {
        "name": "Sport",
        "emoji": "🏃",
        "description": "Sport va outdoor kolleksiyasi.",
        "sort_order": 2,
        "subcategories": [
            {"name": "To'plar", "sources": ["sports-accessories"], "include_keywords": ["ball", "football", "basketball", "volleyball", "golf"], "variant_set": "sport"},
            {"name": "Raketka va Batlar", "sources": ["sports-accessories"], "include_keywords": ["racket", "bat"], "variant_set": "sport"},
            {"name": "Mashg'ulot Anjomlari", "sources": ["sports-accessories"], "include_keywords": ["glove", "helmet", "wicket", "rim", "shuttlecock"], "variant_set": "sport"},
            {"name": "Erkaklar Krossovkasi", "sources": ["mens-shoes"], "variant_set": "sport"},
            {"name": "Ayollar Krossovkasi", "sources": ["womens-shoes"], "variant_set": "sport"},
        ],
    },
    {
        "name": "Erkaklar Kiyimi",
        "emoji": "👔",
        "description": "Erkaklar uchun kiyim va casual style.",
        "sort_order": 3,
        "subcategories": [
            {"name": "Klassik Ko'ylaklar", "sources": ["mens-shirts"], "include_keywords": ["shirt"], "variant_set": "fashion"},
            {"name": "Casual Futbolkalar", "sources": ["mens-shirts", "tops"], "include_keywords": ["tshirt", "frock", "dress"], "variant_set": "fashion"},
            {"name": "Streetwear", "sources": ["mens-shirts", "tops"], "variant_set": "fashion"},
            {"name": "Erkaklar Oyoq Kiyimi", "sources": ["mens-shoes"], "variant_set": "fashion"},
            {"name": "Premium Tanlov", "sources": ["mens-shirts", "mens-shoes", "tops"], "variant_set": "fashion"},
        ],
    },
    {
        "name": "Ayollar Modasi",
        "emoji": "👜",
        "description": "Ayollar uchun moda va kundalik uslub.",
        "sort_order": 4,
        "subcategories": [
            {"name": "Ko'ylaklar", "sources": ["womens-dresses"], "variant_set": "fashion"},
            {"name": "Sumkalar", "sources": ["womens-bags"], "variant_set": "fashion"},
            {"name": "Ayollar Oyoq Kiyimi", "sources": ["womens-shoes"], "variant_set": "fashion"},
            {"name": "Daily Look", "sources": ["womens-dresses", "womens-bags"], "variant_set": "fashion"},
            {"name": "Party Style", "sources": ["womens-dresses", "womens-shoes"], "variant_set": "fashion"},
        ],
    },
    {
        "name": "Soat va Aksessuarlar",
        "emoji": "⌚",
        "description": "Soat, zargarlik va premium aksessuarlar.",
        "sort_order": 5,
        "subcategories": [
            {"name": "Erkaklar Soati", "sources": ["mens-watches"], "variant_set": "accessory"},
            {"name": "Ayollar Soati", "sources": ["womens-watches"], "variant_set": "accessory"},
            {"name": "Ko'zoynaklar", "sources": ["sunglasses"], "variant_set": "accessory"},
            {"name": "Zargarlik", "sources": ["womens-jewellery"], "variant_set": "accessory"},
            {"name": "Premium Aksessuarlar", "sources": ["mens-watches", "womens-watches", "sunglasses"], "variant_set": "accessory"},
        ],
    },
    {
        "name": "Go'zallik",
        "emoji": "✨",
        "description": "Kosmetika, parfyum va teri parvarishi.",
        "sort_order": 6,
        "subcategories": [
            {"name": "Lab va Tirnoq", "sources": ["beauty"], "include_keywords": ["lipstick", "nail", "powder"], "variant_set": "beauty"},
            {"name": "Ko'z Makiyaji", "sources": ["beauty"], "include_keywords": ["mascara", "eyeshadow"], "variant_set": "beauty"},
            {"name": "Atirlar", "sources": ["fragrances"], "variant_set": "beauty"},
            {"name": "Teri Parvarishi", "sources": ["skin-care"], "variant_set": "beauty"},
            {"name": "Beauty Setlar", "sources": ["beauty", "fragrances", "skin-care"], "variant_set": "beauty"},
        ],
    },
    {
        "name": "Uy Interyeri",
        "emoji": "🛋",
        "description": "Mebel va uy dekoratsiyasi tanlovi.",
        "sort_order": 7,
        "subcategories": [
            {"name": "Yumshoq Mebel", "sources": ["furniture"], "include_keywords": ["sofa", "chair", "bed"], "variant_set": "home"},
            {"name": "Stol va Saqlash", "sources": ["furniture"], "include_keywords": ["table", "sink"], "variant_set": "home"},
            {"name": "Dekor Elementlar", "sources": ["home-decoration"], "include_keywords": ["frame", "showpiece", "plant", "pot", "swing"], "variant_set": "home"},
            {"name": "Chiroqlar va Yorug'lik", "sources": ["home-decoration"], "include_keywords": ["lamp"], "variant_set": "home"},
            {"name": "Premium Interyer", "sources": ["furniture", "home-decoration"], "variant_set": "home"},
        ],
    },
    {
        "name": "Oshxona",
        "emoji": "🍳",
        "description": "Oshxona anjomlari va texnikalari.",
        "sort_order": 8,
        "subcategories": [
            {"name": "Pichoq va Kesish", "sources": ["kitchen-accessories"], "include_keywords": ["knife", "board", "slicer", "peeler", "grater"], "variant_set": "kitchen"},
            {"name": "Pishirish Idishlari", "sources": ["kitchen-accessories"], "include_keywords": ["wok", "pan", "pot", "stove"], "variant_set": "kitchen"},
            {"name": "Blender va Texnika", "sources": ["kitchen-accessories"], "include_keywords": ["blender", "microwave"], "variant_set": "kitchen"},
            {"name": "Servis Anjomlari", "sources": ["kitchen-accessories"], "include_keywords": ["cup", "glass", "fork", "spoon", "plate", "mug"], "variant_set": "kitchen"},
            {"name": "Organayzer va Yordamchi", "sources": ["kitchen-accessories"], "include_keywords": ["tray", "stand", "rack", "sieve", "strainer", "tongs", "spatula", "whisk", "turner"], "variant_set": "kitchen"},
        ],
    },
    {
        "name": "Oziq-ovqat",
        "emoji": "🥑",
        "description": "Kundalik oziq-ovqat va ichimliklar.",
        "sort_order": 9,
        "subcategories": [
            {"name": "Mevalar", "sources": ["groceries"], "include_keywords": ["apple", "kiwi", "lemon", "mulberry", "strawberry"], "variant_set": "grocery"},
            {"name": "Sabzavotlar", "sources": ["groceries"], "include_keywords": ["cucumber", "pepper", "chili", "potatoes", "onions"], "variant_set": "grocery"},
            {"name": "Ichimliklar", "sources": ["groceries"], "include_keywords": ["juice", "milk", "water", "soft", "coffee"], "variant_set": "grocery"},
            {"name": "Protein va Go'sht", "sources": ["groceries"], "include_keywords": ["beef", "chicken", "fish", "eggs", "protein"], "variant_set": "grocery"},
            {"name": "Kundalik Mahsulotlar", "sources": ["groceries"], "include_keywords": ["oil", "honey", "rice", "cat food", "dog food", "ice cream", "tissue"], "variant_set": "grocery"},
        ],
    },
    {
        "name": "Transport",
        "emoji": "🏍",
        "description": "Avto va moto mahsulotlari.",
        "sort_order": 10,
        "subcategories": [
            {"name": "Mototsikllar", "sources": ["motorcycle"], "variant_set": "transport"},
            {"name": "Sedanlar", "sources": ["vehicle"], "include_keywords": ["charger", "hornet"], "variant_set": "transport"},
            {"name": "Oilaviy Avto", "sources": ["vehicle"], "include_keywords": ["touring", "durango", "pacifica"], "variant_set": "transport"},
            {"name": "Performance Avto", "sources": ["vehicle", "motorcycle"], "include_keywords": ["sport", "charger", "z800", "motogp"], "variant_set": "transport"},
            {"name": "Premium Drive", "sources": ["vehicle", "motorcycle"], "variant_set": "transport"},
        ],
    },
]


def usd_to_uzs(value):
    amount = Decimal(str(value)) * USD_TO_UZS
    return int((amount / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 1000)


def truncate_text(value, limit=255):
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def build_sizes(source_category):
    if source_category in {"mens-shirts", "tops", "womens-dresses"}:
        return CLOTHING_SIZES
    if source_category in {"mens-shoes", "womens-shoes"}:
        return SHOE_SIZES
    return []


def build_base_features(item):
    features = []
    for field in ("brand", "warrantyInformation", "shippingInformation", "returnPolicy", "availabilityStatus"):
        value = item.get(field)
        if not value:
            continue
        if field == "brand":
            features.append(f"Brend: {value}")
        else:
            features.append(value)
    if item.get("minimumOrderQuantity"):
        features.append(f"Minimal buyurtma: {item['minimumOrderQuantity']} ta")
    if item.get("weight"):
        features.append(f"Og'irligi: {item['weight']}")
    return features


def fetch_products():
    try:
        request = Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except URLError as exc:
        raise CommandError(f"Seed ma'lumotlarini yuklab bo'lmadi: {exc}") from exc

    products = payload.get("products") or []
    if not products:
        raise CommandError("API mahsulot qaytarmadi.")
    return products


def keyword_match(text, keywords):
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in keywords)


def select_base_products(source_products, subcategory_config):
    scoped = [item for item in source_products if item.get("category") in subcategory_config["sources"]]
    include_keywords = subcategory_config.get("include_keywords") or []
    exclude_keywords = subcategory_config.get("exclude_keywords") or []

    if include_keywords:
        filtered = [item for item in scoped if keyword_match(item.get("title"), include_keywords)]
        if filtered:
            scoped = filtered

    if exclude_keywords:
        filtered = [item for item in scoped if not keyword_match(item.get("title"), exclude_keywords)]
        if filtered:
            scoped = filtered

    if not scoped:
        raise CommandError(f"{subcategory_config['name']} uchun source mahsulot topilmadi.")

    return scoped


def build_variant_payload(base_item, profile, category, subcategory_name, index):
    base_price = Decimal(str(base_item.get("price") or 0))
    variant_price = usd_to_uzs(base_price * profile["multiplier"])
    old_price = int((variant_price * 112) / 100) if index % 3 in {1, 2} else None
    base_rating = float(base_item.get("rating") or 4.0)
    rating = min(5.0, round(base_rating + (index % 3) * 0.1, 1))
    reviews_count = max(18, len(base_item.get("reviews") or [])) * 14 + index * 9
    stock = max(3, int(base_item.get("stock") or 10) + profile["stock_delta"])
    image_url = (base_item.get("images") or [base_item.get("thumbnail")])[0] or base_item.get("thumbnail") or ""
    base_description = base_item.get("description") or base_item.get("title") or ""
    variant_name = f"{base_item['title']} {profile['label']}"

    features = build_base_features(base_item)
    features.extend(
        [
            profile["feature"],
            f"Subkategoriya: {subcategory_name}",
            f"Variant seriya: {profile['label']}",
        ]
    )

    if base_item.get("dimensions"):
        dimensions = base_item["dimensions"]
        features.append(
            "O'lchami: "
            f"{dimensions.get('width', 0)} x {dimensions.get('height', 0)} x {dimensions.get('depth', 0)}"
        )

    badge = Product.BADGE_TOP if rating >= 4.7 else Product.BADGE_DISCOUNT if old_price else Product.BADGE_BESTSELLER

    return {
        "category": category,
        "subcategory": subcategory_name,
        "brand": base_item.get("brand") or "Generic",
        "name": variant_name,
        "slug": slugify(f"{category.name}-{subcategory_name}-{base_item['id']}-{index}-{profile['label']}"),
        "short_description": truncate_text(f"{base_description} {profile['feature']}."),
        "description": " ".join(
            part
            for part in [
                base_description,
                profile["feature"],
                base_item.get("shippingInformation"),
                base_item.get("returnPolicy"),
            ]
            if part
        ),
        "price": variant_price,
        "old_price": old_price if old_price and old_price > variant_price else None,
        "rating": rating,
        "reviews_count": reviews_count,
        "stock": stock,
        "badge": badge,
        "image_key": image_url,
        "colors": CATEGORY_COLORS.get(category.name, ["#111827", "#e5e7eb"]),
        "sizes": build_sizes(base_item.get("category")),
        "features": features[:6],
        "is_featured": index < 2,
        "featured_order": 0,
        "is_active": True,
    }


class Command(BaseCommand):
    help = "Seed a large catalog with 10 categories, 5 subcategories each, and 10 products per subcategory."

    @transaction.atomic
    def handle(self, *args, **options):
        source_products = fetch_products()

        Product.objects.all().delete()
        Category.objects.all().delete()

        created_categories = 0
        created_products = 0
        featured_order = 1

        for category_config in CATEGORY_CONFIGS:
            category = Category.objects.create(
                name=category_config["name"],
                emoji=category_config["emoji"],
                description=category_config["description"],
                sort_order=category_config["sort_order"],
                is_active=True,
            )
            created_categories += 1

            for subcategory_config in category_config["subcategories"]:
                base_products = select_base_products(source_products, subcategory_config)
                variant_profiles = VARIANT_SETS[subcategory_config["variant_set"]]

                for index in range(PRODUCTS_PER_SUBCATEGORY):
                    base_item = base_products[index % len(base_products)]
                    profile = variant_profiles[index]
                    payload = build_variant_payload(
                        base_item=base_item,
                        profile=profile,
                        category=category,
                        subcategory_name=subcategory_config["name"],
                        index=index,
                    )
                    payload["featured_order"] = featured_order
                    Product.objects.create(**payload)
                    created_products += 1
                    featured_order += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog seeded successfully: {created_categories} kategoriya, {created_products} mahsulot."
            )
        )
