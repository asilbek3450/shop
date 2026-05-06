from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def chunk_buttons(labels, size=2):
    rows = []
    for index in range(0, len(labels), size):
        rows.append([KeyboardButton(text=label) for label in labels[index:index + size]])
    return rows


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🔥 Tavsiyalar")],
            [KeyboardButton(text="🛒 Savat"), KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="🌐 Sayt"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def categories_keyboard(categories):
    labels = [f"{category.emoji} {category.name}" for category in categories]
    return ReplyKeyboardMarkup(
        keyboard=chunk_buttons(labels) + [[KeyboardButton(text="⬅️ Bosh menyu")]],
        resize_keyboard=True,
    )


def subcategories_keyboard(subcategories):
    labels = [f"📂 {name}" for name in subcategories]
    rows = chunk_buttons(labels)
    rows.append([KeyboardButton(text="🛒 Savat"), KeyboardButton(text="📦 Buyurtmalarim")])
    rows.append([KeyboardButton(text="⬅️ Kategoriyalar")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def products_keyboard(products, back_label="⬅️ Kategoriyalar"):
    labels = [product_button_label(product.name) for product in products]
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="🛒 Savat"), KeyboardButton(text="✅ Buyurtma berish")])
    rows.append([KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="🔥 Tavsiyalar")])
    rows.append([KeyboardButton(text=back_label), KeyboardButton(text="⬅️ Bosh menyu")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def product_button_label(name):
    compact = (name or "").strip()
    if len(compact) > 42:
        compact = compact[:39].rstrip() + "..."
    return f"🛍 {compact}"


def cart_actions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Buyurtma berish"), KeyboardButton(text="🧹 Savatni tozalash")],
            [KeyboardButton(text="⬅️ Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def phone_request_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="⬅️ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard():
    return ReplyKeyboardRemove()


def product_actions_keyboard(product_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Savatga qo'shish", callback_data=f"add:{product_id}"),
                InlineKeyboardButton(text="🌐 Saytda ko'rish", callback_data=f"site:{product_id}"),
            ]
        ]
    )


def delivery_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚚 Standart (25 000 so'm)", callback_data="delivery:standard")],
            [InlineKeyboardButton(text="⚡ Tezkor (50 000 so'm)", callback_data="delivery:express")],
            [InlineKeyboardButton(text="🏪 Do'kondan olib ketish (Bepul)", callback_data="delivery:pickup")],
        ]
    )


def payment_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Karta", callback_data="payment:card")],
            [InlineKeyboardButton(text="📱 Click / Payme", callback_data="payment:click")],
            [InlineKeyboardButton(text="💵 Naqd to'lov", callback_data="payment:cash")],
        ]
    )


def confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="order:confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="order:cancel")],
        ]
    )
