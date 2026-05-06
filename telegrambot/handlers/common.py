from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async
from django.conf import settings

from catalog.models import Category, Product
from orders.models import Order
from orders.services.checkout import DELIVERY_COSTS, create_order
from telegrambot.keyboards.reply import (
    cart_actions_keyboard,
    categories_keyboard,
    confirm_keyboard,
    delivery_keyboard,
    main_menu_keyboard,
    payment_keyboard,
    phone_request_keyboard,
    product_actions_keyboard,
    remove_keyboard,
    subcategories_keyboard,
)
from telegrambot.models import TelegramProfile


router = Router(name="common")


class CheckoutStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_note = State()


# ──────────────────────────── DB helpers ────────────────────────────


@sync_to_async
def upsert_profile(message: Message):
    user = message.from_user
    profile, _ = TelegramProfile.objects.update_or_create(
        user_id=user.id,
        defaults={
            "chat_id": message.chat.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "language_code": user.language_code or "",
            "is_blocked": False,
        },
    )
    return profile


@sync_to_async
def get_profile(user_id):
    return TelegramProfile.objects.filter(user_id=user_id).first()


@sync_to_async
def save_profile(profile, **fields):
    for key, value in fields.items():
        setattr(profile, key, value)
    profile.save(update_fields=list(fields.keys()) + ["last_seen_at"])


@sync_to_async
def get_categories():
    return list(Category.objects.filter(is_active=True).order_by("sort_order", "name"))


@sync_to_async
def get_subcategories_for(category_name):
    qs = (
        Product.objects.filter(is_active=True, category__name=category_name)
        .exclude(subcategory="")
        .values_list("subcategory", flat=True)
        .distinct()
    )
    return sorted(set(qs))


@sync_to_async
def get_products_for(category_name, subcategory=None, limit=10):
    queryset = Product.objects.select_related("category").filter(
        is_active=True, category__is_active=True, category__name=category_name
    )
    if subcategory:
        queryset = queryset.filter(subcategory=subcategory)
    return list(queryset.order_by("featured_order", "name")[:limit])


@sync_to_async
def get_featured_products():
    return list(
        Product.objects.select_related("category")
        .filter(is_active=True, is_featured=True, category__is_active=True)
        .order_by("featured_order", "name")[:6]
    )


@sync_to_async
def get_product(product_id):
    return Product.objects.select_related("category").filter(id=product_id, is_active=True).first()


@sync_to_async
def get_recent_orders(user_id, limit=5):
    return list(Order.objects.filter(telegram_user_id=user_id).order_by("-created_at")[:limit])


@sync_to_async
def submit_order_for(profile: TelegramProfile, customer, items, delivery_method, payment_method):
    order = create_order(
        customer=customer,
        items=items,
        delivery_method=delivery_method,
        payment_method=payment_method,
        source=Order.SOURCE_BOT,
        telegram={"user_id": profile.user_id, "username": profile.username},
    )
    profile.cart = []
    profile.pending_order = {}
    profile.save(update_fields=["cart", "pending_order", "last_seen_at"])
    return order


# ──────────────────────────── Formatting ────────────────────────────


def format_price(amount):
    return f"{int(amount):,} so'm".replace(",", " ")


def product_caption(product):
    site_url = settings.SITE_URL.rstrip("/")
    lines = [
        f"<b>{product.name}</b>",
        f"🏷 Brend: {product.brand}",
        f"📂 {product.category.emoji} {product.category.name}"
        + (f" → {product.subcategory}" if product.subcategory else ""),
        f"💰 Narx: {format_price(product.price)}",
    ]
    if product.old_price and product.old_price > product.price:
        lines.append(f"💸 Eski narx: <s>{format_price(product.old_price)}</s>")
    lines.append(f"⭐ {product.rating} ({product.reviews_count} sharh)")
    lines.append(f"📦 Omborda: {product.stock} ta")
    if product.badge:
        lines.append(f"🔥 {product.badge}")
    if product.short_description:
        lines.append("")
        lines.append(product.short_description)
    lines.append("")
    lines.append(f"🔗 {site_url}/products/{product.slug}/")
    return "\n".join(lines)


def cart_summary_text(cart):
    if not cart:
        return "🧺 Savat bo'sh."
    lines = ["🧺 <b>Savatdagi mahsulotlar:</b>", ""]
    total = 0
    for index, item in enumerate(cart, start=1):
        line_total = int(item["price"]) * int(item.get("qty", 1))
        total += line_total
        lines.append(
            f"{index}. {item['name']} × {item.get('qty', 1)} — {format_price(line_total)}"
        )
    lines.append("")
    lines.append(f"💰 Jami: <b>{format_price(total)}</b>")
    return "\n".join(lines)


def is_remote_image(value):
    return isinstance(value, str) and value.lower().startswith(("http://", "https://"))


async def send_product_card(message: Message, product):
    caption = product_caption(product)
    keyboard = product_actions_keyboard(product.id)
    if is_remote_image(product.image_key):
        try:
            await message.answer_photo(product.image_key, caption=caption, reply_markup=keyboard)
            return
        except Exception:
            pass
    await message.answer(caption, reply_markup=keyboard, disable_web_page_preview=False)


# ──────────────────────────── Start / main menu ────────────────────────────


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await upsert_profile(message)
    await message.answer(
        "👋 NEXUS botiga xush kelibsiz!\n\n"
        "Kategoriyalar bo'yicha mahsulotlarni ko'ring, savatga qo'shing va to'g'ridan-to'g'ri "
        "shu yerdan buyurtma bering. Buyurtmalar admin panelga tushadi.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text.in_({"⬅️ Bosh menyu", "🏠 Bosh menyu"}))
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyuga qaytdik.", reply_markup=main_menu_keyboard())


# ──────────────────────────── Catalog flow ────────────────────────────


@router.message(F.text == "🛍 Katalog")
async def show_catalog(message: Message):
    categories = await get_categories()
    if not categories:
        await message.answer("Katalog bo'sh.", reply_markup=main_menu_keyboard())
        return
    await message.answer(
        "Kerakli kategoriyani tanlang:",
        reply_markup=categories_keyboard(categories),
    )


@router.message(F.text == "⬅️ Kategoriyalar")
async def back_to_categories(message: Message):
    profile = await get_profile(message.from_user.id)
    if profile:
        await save_profile(profile, selected_subcategory="")
    categories = await get_categories()
    await message.answer("Kategoriyalar:", reply_markup=categories_keyboard(categories))


@router.message(F.text == "🔥 Tavsiyalar")
async def show_featured(message: Message):
    products = await get_featured_products()
    if not products:
        await message.answer("Hozircha tavsiyalar yo'q.", reply_markup=main_menu_keyboard())
        return
    await message.answer("🔥 Haftaning eng kuchli tavsiyalari:", reply_markup=main_menu_keyboard())
    for product in products:
        await send_product_card(message, product)


@router.message(F.text == "🌐 Sayt")
async def show_site(message: Message):
    site = settings.SITE_URL.rstrip("/")
    await message.answer(
        f"🌐 Website: {site}\n🛍 Do'kon: {site}/shop/",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "ℹ️ Yordam")
async def help_message(message: Message):
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "• 🛍 Katalog — kategoriyalar va subkategoriyalar\n"
        "• 🔥 Tavsiyalar — featured mahsulotlar\n"
        "• 🛒 Savat — joriy savat va buyurtma berish\n"
        "• 📦 Buyurtmalarim — buyurtma tarixi\n"
        "• 🌐 Sayt — website havolasi\n",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────── Subcategory selection ────────────────────────────


@router.message(F.text.startswith("📂 "))
async def show_subcategory_products(message: Message):
    profile = await get_profile(message.from_user.id)
    if not profile or not profile.selected_category:
        await message.answer(
            "Avval kategoriyani tanlang.",
            reply_markup=categories_keyboard(await get_categories()),
        )
        return

    subcategory = message.text.removeprefix("📂 ").strip()
    products = await get_products_for(profile.selected_category.name, subcategory=subcategory)
    if not products:
        await message.answer("Bu subkategoriyada mahsulot yo'q.")
        return

    await save_profile(profile, selected_subcategory=subcategory)
    await message.answer(
        f"<b>{profile.selected_category.emoji} {profile.selected_category.name}</b> → {subcategory}\n"
        f"Topildi: {len(products)} ta",
        reply_markup=subcategories_keyboard(
            await get_subcategories_for(profile.selected_category.name)
        ),
    )
    for product in products:
        await send_product_card(message, product)


@router.message(F.text.regexp(r"^.+\s.+$"))
async def show_category(message: Message):
    categories = await get_categories()
    labels = {f"{category.emoji} {category.name}": category for category in categories}
    category = labels.get(message.text)
    if not category:
        return

    profile = await get_profile(message.from_user.id)
    if profile:
        await save_profile(profile, selected_category=category, selected_subcategory="")

    subs = await get_subcategories_for(category.name)
    if not subs:
        products = await get_products_for(category.name)
        if not products:
            await message.answer(
                "Bu kategoriyada mahsulot yo'q.",
                reply_markup=categories_keyboard(categories),
            )
            return
        await message.answer(
            f"{category.emoji} {category.name} bo'yicha mahsulotlar:",
            reply_markup=categories_keyboard(categories),
        )
        for product in products:
            await send_product_card(message, product)
        return

    await message.answer(
        f"<b>{category.emoji} {category.name}</b>\n"
        f"Subkategoriyalardan birini tanlang ({len(subs)} ta):",
        reply_markup=subcategories_keyboard(subs),
    )


# ──────────────────────────── Cart ────────────────────────────


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    product = await get_product(product_id)
    profile = await get_profile(callback.from_user.id)
    if not product or not profile:
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return

    cart = list(profile.cart or [])
    for item in cart:
        if item.get("product_id") == product.id:
            item["qty"] = int(item.get("qty", 1)) + 1
            break
    else:
        cart.append(
            {
                "product_id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": product.price,
                "qty": 1,
            }
        )

    await save_profile(profile, cart=cart)
    await callback.answer(f"✅ {product.name} savatga qo'shildi", show_alert=False)


@router.callback_query(F.data.startswith("site:"))
async def open_site(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    product = await get_product(product_id)
    if not product:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    site = settings.SITE_URL.rstrip("/")
    await callback.answer()
    await callback.message.answer(f"🔗 {site}/products/{product.slug}/")


@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    profile = await get_profile(message.from_user.id)
    cart = (profile.cart if profile else []) or []
    text = cart_summary_text(cart)
    await message.answer(
        text,
        reply_markup=cart_actions_keyboard() if cart else main_menu_keyboard(),
    )


@router.message(F.text == "🧹 Savatni tozalash")
async def clear_cart(message: Message):
    profile = await get_profile(message.from_user.id)
    if profile:
        await save_profile(profile, cart=[])
    await message.answer("🧹 Savat tozalandi.", reply_markup=main_menu_keyboard())


# ──────────────────────────── Order flow ────────────────────────────


@router.message(F.text == "✅ Buyurtma berish")
async def begin_order(message: Message, state: FSMContext):
    profile = await get_profile(message.from_user.id)
    cart = (profile.cart if profile else []) or []
    if not cart:
        await message.answer("Savat bo'sh. Avval mahsulot qo'shing.", reply_markup=main_menu_keyboard())
        return

    await message.answer(
        cart_summary_text(cart) + "\n\nYetkazib berish usulini tanlang:",
        reply_markup=delivery_keyboard(),
    )
    await state.update_data(stage="delivery")


@router.callback_query(F.data.startswith("delivery:"))
async def pick_delivery(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split(":", 1)[1]
    if method not in DELIVERY_COSTS:
        await callback.answer("Noto'g'ri usul.", show_alert=True)
        return
    await state.update_data(delivery=method)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"🚚 Yetkazish: <b>{dict(Order.DELIVERY_CHOICES)[method]}</b>\n\nTo'lov usulini tanlang:",
        reply_markup=payment_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("payment:"))
async def pick_payment(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split(":", 1)[1]
    if not dict(Order.PAYMENT_CHOICES).get(method):
        await callback.answer("Noto'g'ri usul.", show_alert=True)
        return
    await state.update_data(payment=method)
    await callback.message.edit_reply_markup(reply_markup=None)
    profile = await get_profile(callback.from_user.id)
    default_name = " ".join(filter(None, [profile.first_name, profile.last_name])).strip() if profile else ""
    prompt = "👤 Ism-familiyangizni yuboring"
    if default_name:
        prompt += f"\n(masalan: <i>{default_name}</i>)"
    await callback.message.answer(prompt, reply_markup=remove_keyboard())
    await state.set_state(CheckoutStates.waiting_name)
    await callback.answer()


@router.message(CheckoutStates.waiting_name, F.text)
async def capture_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Ism juda qisqa. Qaytadan yuboring:")
        return
    parts = full_name.split(maxsplit=1)
    await state.update_data(first_name=parts[0], last_name=parts[1] if len(parts) > 1 else "")
    await message.answer(
        "📱 Endi telefon raqamingizni yuboring (yoki tugmadan foydalaning):",
        reply_markup=phone_request_keyboard(),
    )
    await state.set_state(CheckoutStates.waiting_phone)


@router.message(CheckoutStates.waiting_phone, F.text == "⬅️ Bekor qilish")
async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())


@router.message(CheckoutStates.waiting_phone, F.contact)
async def capture_phone_contact(message: Message, state: FSMContext):
    phone = (message.contact.phone_number or "").strip() if message.contact else ""
    await _continue_after_phone(message, state, phone)


@router.message(CheckoutStates.waiting_phone, F.text)
async def capture_phone_text(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 9:
        await message.answer("Telefon raqami noto'g'ri ko'rinadi. Qaytadan yuboring:")
        return
    await _continue_after_phone(message, state, phone)


async def _continue_after_phone(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    data = await state.get_data()
    if data.get("delivery") == Order.DELIVERY_PICKUP:
        await state.update_data(address="Do'kondan olib ketish")
        await message.answer(
            "📝 Buyurtmaga qo'shimcha izoh bormi? Bo'lmasa <b>—</b> deb yozing:",
            reply_markup=remove_keyboard(),
        )
        await state.set_state(CheckoutStates.waiting_note)
        return

    await message.answer(
        "🏠 Yetkazib beriladigan manzilni yuboring (shahar, ko'cha, uy):",
        reply_markup=remove_keyboard(),
    )
    await state.set_state(CheckoutStates.waiting_address)


@router.message(CheckoutStates.waiting_address, F.text)
async def capture_address(message: Message, state: FSMContext):
    address = (message.text or "").strip()
    if len(address) < 4:
        await message.answer("Manzil juda qisqa. Aniqroq yozing:")
        return
    await state.update_data(address=address)
    await message.answer("📝 Buyurtmaga qo'shimcha izoh bormi? Bo'lmasa <b>—</b> deb yozing:")
    await state.set_state(CheckoutStates.waiting_note)


@router.message(CheckoutStates.waiting_note, F.text)
async def capture_note_and_confirm(message: Message, state: FSMContext):
    note = (message.text or "").strip()
    if note in {"-", "—", "yo'q", "yo`q"}:
        note = ""
    await state.update_data(note=note)

    profile = await get_profile(message.from_user.id)
    cart = (profile.cart if profile else []) or []
    data = await state.get_data()
    delivery = data.get("delivery", Order.DELIVERY_STANDARD)
    payment = data.get("payment", Order.PAYMENT_CARD)

    subtotal = sum(int(item["price"]) * int(item.get("qty", 1)) for item in cart)
    delivery_cost = DELIVERY_COSTS[delivery]
    total = subtotal + delivery_cost

    summary = [
        "<b>📦 Buyurtmani tasdiqlang</b>",
        "",
        cart_summary_text(cart),
        "",
        f"👤 Mijoz: {data.get('first_name', '')} {data.get('last_name', '')}".strip(),
        f"📱 Telefon: {data.get('phone', '')}",
        f"🏠 Manzil: {data.get('address', '')}",
        f"📝 Izoh: {note or '—'}",
        f"🚚 Yetkazish: {dict(Order.DELIVERY_CHOICES)[delivery]} ({format_price(delivery_cost)})",
        f"💳 To'lov: {dict(Order.PAYMENT_CHOICES)[payment]}",
        "",
        f"💰 Umumiy: <b>{format_price(total)}</b>",
    ]
    await message.answer("\n".join(summary), reply_markup=confirm_keyboard())


@router.callback_query(F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    profile = await get_profile(callback.from_user.id)
    cart = (profile.cart if profile else []) or []
    if not cart:
        await callback.answer("Savat bo'sh.", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    customer = {
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
        "note": data.get("note", ""),
    }
    delivery = data.get("delivery", Order.DELIVERY_STANDARD)
    payment = data.get("payment", Order.PAYMENT_CARD)

    try:
        order = await submit_order_for(profile, customer, cart, delivery, payment)
    except Exception as exc:
        await callback.answer("Xatolik", show_alert=True)
        await callback.message.answer(f"⚠️ Buyurtma yuborilmadi: {exc}", reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "🎉 <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"Buyurtma raqami: <code>{order.code}</code>\n"
        f"💰 Jami: <b>{format_price(order.total)}</b>\n\n"
        "Tez orada operator siz bilan bog'lanadi.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("✅ Yuborildi")


# ──────────────────────────── Order history ────────────────────────────


@router.message(F.text == "📦 Buyurtmalarim")
async def show_orders(message: Message):
    orders = await get_recent_orders(message.from_user.id)
    if not orders:
        await message.answer("Sizda hali buyurtma yo'q.", reply_markup=main_menu_keyboard())
        return
    lines = ["📦 <b>So'nggi buyurtmalaringiz:</b>", ""]
    for order in orders:
        lines.append(
            f"• <code>{order.code}</code> — {format_price(order.total)} — {order.get_status_display()}"
        )
    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())
