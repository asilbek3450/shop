"""Web ↔ Telegram verification flow.

When a user visits t.me/<bot>?start=<token>:
  1. The common /start handler detects the token payload and calls begin_verification().
  2. We look up an active PhoneVerification by token.
  3. We ask for the user's contact (request_contact).
  4. We compare the shared phone with the one entered on the website.
  5. On match, we issue a 6-digit code and DM it back; the website then verifies it.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async

from accounts.services import attach_telegram_to_verification, find_active_verification
from accounts.utils import normalize_phone

router = Router(name="verification")


class VerifyStates(StatesGroup):
    waiting_contact = State()


def _contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefonimni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@sync_to_async
def _lookup(token):
    return find_active_verification(token)


@sync_to_async
def _attach(verification, **kwargs):
    return attach_telegram_to_verification(verification, **kwargs)


async def begin_verification(message: Message, state: FSMContext, token: str) -> bool:
    """Entry point invoked from the common /start handler when a payload is present.

    Returns True if a verification was started (so the caller can skip the regular
    welcome message), False if the token was invalid/expired.
    """
    token = (token or "").strip()
    if not token:
        return False

    verification = await _lookup(token)
    if not verification:
        await message.answer(
            "❌ Tasdiqlash havolasi yaroqsiz yoki muddati tugagan.\n"
            "Iltimos saytda qaytadan ro'yxatdan o'ting."
        )
        return True

    await state.set_state(VerifyStates.waiting_contact)
    await state.update_data(token=token)
    await message.answer(
        "👋 Salom! Saytda kiritgan telefon raqamingizni tasdiqlash uchun "
        "<b>Telefonimni yuborish</b> tugmasini bosing.",
        reply_markup=_contact_keyboard(),
    )
    return True


@router.message(VerifyStates.waiting_contact, F.text == "❌ Bekor qilish")
async def cancel_verification(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@router.message(VerifyStates.waiting_contact, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get("token")
    verification = await _lookup(token) if token else None
    if not verification:
        await state.clear()
        await message.answer(
            "❌ Tasdiqlash sessiyasi muddati tugagan. Saytda qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Iltimos faqat <b>o'zingizning</b> raqamingizni yuboring."
        )
        return

    shared = normalize_phone(contact.phone_number)
    expected = verification.phone
    phone_match = shared == expected

    await _attach(
        verification,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        phone_match=phone_match,
    )

    if not phone_match:
        await message.answer(
            f"⚠️ Yuborilgan raqam ({shared or contact.phone_number}) saytdagi raqam bilan mos kelmadi.\n\n"
            "Iltimos saytda kiritgan raqamingiz bilan bir xil Telegram akkauntdan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Raqam tasdiqlandi!\n\n"
        f"Sizning tasdiqlash kodingiz: <b><code>{verification.code}</code></b>\n\n"
        "Bu kodni saytdagi tasdiqlash oynasiga kiriting. Kod 15 daqiqa davomida amal qiladi.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(VerifyStates.waiting_contact)
async def remind_contact(message: Message):
    await message.answer(
        "Iltimos pastdagi <b>📱 Telefonimni yuborish</b> tugmasini bosing.",
        reply_markup=_contact_keyboard(),
    )
