"""
PayTechUZ to'lov tizimini sozlash uchun PDF qo'llanma yaratuvchi script.

Ishga tushirish:
    python scripts/build_payment_guide_pdf.py

Natija: docs/payment_setup_guide.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "docs" / "payment_setup_guide.pdf"


def build_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleX",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    subtitle = ParagraphStyle(
        "Sub",
        parent=base["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#475569"),
        leading=15,
        spaceAfter=12,
    )
    h1 = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=body,
        leftIndent=14,
        bulletIndent=2,
        spaceAfter=2,
    )
    code = ParagraphStyle(
        "Code",
        parent=base["Code"],
        fontName="Courier",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=4,
        spaceAfter=10,
    )
    note = ParagraphStyle(
        "Note",
        parent=body,
        backColor=colors.HexColor("#fef3c7"),
        borderColor=colors.HexColor("#f59e0b"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=4,
        spaceAfter=10,
        textColor=colors.HexColor("#78350f"),
    )
    return {
        "title": title,
        "subtitle": subtitle,
        "h1": h1,
        "h2": h2,
        "body": body,
        "bullet": bullet,
        "code": code,
        "note": note,
    }


def hr():
    return HRFlowable(
        width="100%",
        thickness=0.6,
        color=colors.HexColor("#e2e8f0"),
        spaceBefore=4,
        spaceAfter=8,
    )


def kv_table(rows):
    table = Table(rows, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#ffffff")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build(story, styles):
    S = styles
    P = lambda t, s="body": Paragraph(t, S[s])
    code = lambda t: Paragraph(t.replace("\n", "<br/>").replace(" ", "&nbsp;"), S["code"])

    # ─── Cover ──────────────────────────────────────────────
    story += [
        P("PayTechUZ to'lov tizimini sozlash qo'llanmasi", "title"),
        P("Payme va Click integratsiyasi · Django loyihasi uchun", "subtitle"),
        hr(),
        P("Ushbu qo'llanma ushbu loyihada PayTechUZ kutubxonasi orqali "
          "<b>Payme</b> va <b>Click</b> to'lovlarini sozlash uchun barcha "
          "qadamlarni o'z ichiga oladi: qaysi fayl, qaysi qator va qanday "
          "qiymat yozilishi kerakligi to'liq ko'rsatilgan."),
        Spacer(1, 6),
    ]

    # ─── 1. O'rnatish ───────────────────────────────────────
    story += [
        P("1. Kutubxonani o'rnatish", "h1"),
        P("Loyiha papkasiga kiring va paketni Django qo'llab-quvvatlashi bilan o'rnating:"),
        code("pip install 'paytechuz[django]==0.3.51'"),
        P("Bu paket avtomatik tarzda quyidagi <b>requirements.txt</b> faylida ko'rsatilgan:"),
        code("paytechuz[django]==0.3.51"),
    ]

    # ─── 2. .env ────────────────────────────────────────────
    story += [
        P("2. <b>.env</b> fayliga maxfiy kalitlarni yozish", "h1"),
        P("Loyiha root papkasidagi <b>.env</b> faylga quyidagi qatorlarni qo'shing. "
          "Bo'sh qiymatlarni merchant kabinetdan olingan haqiqiy qiymatlar bilan "
          "almashtiring:"),
        code(
            "# ─── Payment: Payme ───────────────────────────────────────\n"
            "PAYME_ID=                       # Merchant ID (Payme business kabinet)\n"
            "PAYME_KEY=                      # Maxfiy kalit (test yoki prod)\n"
            "PAYME_TEST_MODE=true            # Production'da false\n\n"
            "# ─── Payment: Click ───────────────────────────────────────\n"
            "CLICK_SERVICE_ID=               # Servis ID raqami\n"
            "CLICK_MERCHANT_ID=              # Merchant ID raqami\n"
            "CLICK_MERCHANT_USER_ID=         # Merchant user ID\n"
            "CLICK_SECRET_KEY=               # Maxfiy kalit\n"
            "CLICK_TEST_MODE=true            # Production'da false"
        ),
        P("Bu qiymatlarni qayerdan olish kerakligi:", "h2"),
        P("• <b>Payme</b>: business.payme.uz → Sozlamalar → API kalitlar (test/live)", "bullet"),
        P("• <b>Click</b>: my.click.uz → Merchant kabinet → Servis va kalit ma'lumotlari", "bullet"),
        Spacer(1, 4),
        Paragraph(
            "<b>Diqqat:</b> .env faylni hech qachon git'ga commit qilmang. "
            "Loyihada .gitignore bu faylni allaqachon ignore qiladi.",
            S["note"],
        ),
    ]

    story += [PageBreak()]

    # ─── 3. settings.py ─────────────────────────────────────
    story += [
        P("3. <b>config/settings.py</b> da konfiguratsiya", "h1"),
        P("Quyidagilar bu loyihada allaqachon yozilgan, lekin tushunish uchun "
          "ma'lumot sifatida keltirilmoqda."),
        P("3.1. INSTALLED_APPS", "h2"),
        P("Quyidagi ikkita ilova ro'yxatda bo'lishi shart:"),
        code(
            "INSTALLED_APPS = [\n"
            "    # ...\n"
            "    'orders',\n"
            "    'payment',                              # ← bizning ilova\n"
            "    'telegrambot',\n"
            "    'paytechuz.integrations.django',        # ← PayTechUZ\n"
            "]"
        ),
        P("3.2. PAYTECHUZ konfiguratsiyasi", "h2"),
        P("Bu blok env-variables'dan o'qiydi — siz settings.py'ni o'zgartirmaysiz, "
          "faqat .env'dagi qiymatlarni o'zgartirasiz:"),
        code(
            "PAYTECHUZ = {\n"
            "    'PAYME': {\n"
            "        'PAYME_ID':       env('PAYME_ID', ''),\n"
            "        'PAYME_KEY':      env('PAYME_KEY', ''),\n"
            "        'ACCOUNT_MODEL':  'payment.models.Invoice',\n"
            "        'ACCOUNT_FIELD':  'id',\n"
            "        'AMOUNT_FIELD':   'amount',\n"
            "        'ONE_TIME_PAYMENT': True,\n"
            "        'IS_TEST_MODE':   env_bool('PAYME_TEST_MODE', True),\n"
            "    },\n"
            "    'CLICK': {\n"
            "        'SERVICE_ID':         env('CLICK_SERVICE_ID', ''),\n"
            "        'MERCHANT_ID':        env('CLICK_MERCHANT_ID', ''),\n"
            "        'MERCHANT_USER_ID':   env('CLICK_MERCHANT_USER_ID', ''),\n"
            "        'SECRET_KEY':         env('CLICK_SECRET_KEY', ''),\n"
            "        'ACCOUNT_MODEL':      'payment.models.Invoice',\n"
            "        'ACCOUNT_FIELD':      'id',\n"
            "        'COMMISSION_PERCENT': 0.0,\n"
            "        'ONE_TIME_PAYMENT':   True,\n"
            "        'IS_TEST_MODE':       env_bool('CLICK_TEST_MODE', True),\n"
            "    },\n"
            "}"
        ),
    ]

    # ─── 4. URL'lar ─────────────────────────────────────────
    story += [
        PageBreak(),
        P("4. URL'larni rouqniltirish", "h1"),
        P("<b>config/urls.py</b> da quyidagi qator bo'lishi kerak:"),
        code(
            "urlpatterns = [\n"
            "    path('admin/', admin.site.urls),\n"
            "    path('accounts/', include('accounts.urls')),\n"
            "    path('orders/', include('orders.urls')),\n"
            "    path('payment/', include('payment.urls', namespace='payment')),\n"
            "    path('reviews/', include('catalog.urls')),\n"
            "    path('', include('store.urls')),\n"
            "]"
        ),
        P("<b>payment/urls.py</b> ichida 3 ta endpoint registratsiya qilinadi:"),
        code(
            "app_name = 'payment'\n\n"
            "urlpatterns = [\n"
            "    path('create/',         create_payment_link,        name='create'),\n"
            "    path('webhooks/payme/', PaymeWebhookView.as_view(),  name='payme-webhook'),\n"
            "    path('webhooks/click/', ClickWebhookView.as_view(),  name='click-webhook'),\n"
            "]"
        ),
    ]

    # ─── 5. Endpoint'lar jadvali ─────────────────────────────
    story += [
        P("5. Endpoint'lar xulosasi", "h1"),
        kv_table([
            ["Endpoint", "Maqsadi"],
            ["POST /orders/submit/", "Buyurtma yaratadi. Agar to'lov turi 'payme' yoki 'click' bo'lsa, javobda 'payment_url' qaytaradi."],
            ["POST /payment/create/", "Mavjud buyurtma uchun to'lov havolasini yaratadi. Body: {order_code, provider, return_url?}"],
            ["POST /payment/webhooks/payme/", "Payme tomonidan chaqiriladigan webhook. Merchant kabinetda ko'rsatiladi."],
            ["POST /payment/webhooks/click/", "Click tomonidan chaqiriladigan webhook. Merchant kabinetda ko'rsatiladi."],
        ]),
    ]

    # ─── 6. Migration ───────────────────────────────────────
    story += [
        P("6. Ma'lumotlar bazasini yangilash", "h1"),
        P("Yangi <b>Invoice</b> modeli qo'shildi, hamda <b>Order.payment_method</b> "
          "tanlovi (Payme va Click alohida) o'zgartirildi. Migrationlarni qo'llang:"),
        code(
            "python manage.py makemigrations\n"
            "python manage.py migrate"
        ),
        P("Yaratiladigan migrationlar:"),
        P("• <b>orders/migrations/0003_alter_order_payment_method.py</b>", "bullet"),
        P("• <b>payment/migrations/0001_initial.py</b>", "bullet"),
    ]

    # ─── 7. Merchant kabinet ─────────────────────────────────
    story += [
        PageBreak(),
        P("7. Merchant kabinetda webhook URL'larni ko'rsatish", "h1"),
        P("Test rejimida ishlash uchun siz publik URL'ga ega bo'lishingiz kerak. "
          "Lokal mashinadan test qilish uchun <b>ngrok</b> yoki <b>cloudflared</b> "
          "ishlatishingiz mumkin:"),
        code("ngrok http 8000"),
        P("So'ngra olingan publik URL'ni quyidagi joylarda ko'rsating:"),
        P("Payme business kabinet", "h2"),
        kv_table([
            ["Sozlama", "Qiymat"],
            ["Endpoint URL", "https://<sizning-domain>/payment/webhooks/payme/"],
            ["HTTP Method", "POST"],
            ["Account field", "id (Invoice.id)"],
        ]),
        Spacer(1, 4),
        P("Click merchant kabinet", "h2"),
        kv_table([
            ["Sozlama", "Qiymat"],
            ["Prepare/Complete URL", "https://<sizning-domain>/payment/webhooks/click/"],
            ["HTTP Method", "POST"],
            ["Account field", "id (Invoice.id)"],
        ]),
    ]

    # ─── 8. Foydalanish ─────────────────────────────────────
    story += [
        P("8. Frontend'dan qanday foydalanish", "h1"),
        P("8.1. Buyurtma yaratish bilan birga to'lov havolasi", "h2"),
        P("submit_order javobida agar payment_method 'payme' yoki 'click' bo'lsa, "
          "<b>payment_url</b> avtomatik qaytariladi:"),
        code(
            "// frontend (savatdan checkout):\n"
            "const res = await fetch('/orders/submit/', {\n"
            "    method: 'POST',\n"
            "    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},\n"
            "    body: JSON.stringify({\n"
            "        customer: {first_name, phone, address, ...},\n"
            "        items: cartItems,\n"
            "        delivery_method: 'standard',\n"
            "        payment_method: 'payme',     // yoki 'click'\n"
            "    })\n"
            "});\n"
            "const data = await res.json();\n"
            "if (data.payment_url) {\n"
            "    window.location.href = data.payment_url;\n"
            "}"
        ),
        P("8.2. Mavjud buyurtma uchun to'lov havolasi", "h2"),
        P("Agar buyurtma allaqachon yaratilgan bo'lsa va keyinroq to'lov "
          "havolasi kerak bo'lsa:"),
        code(
            "POST /payment/create/\n"
            "Content-Type: application/json\n\n"
            "{\n"
            "    \"order_code\": \"ORD-XXXXXXXX\",\n"
            "    \"provider\":   \"payme\",      // yoki \"click\"\n"
            "    \"return_url\": \"https://sayt.uz/orders/\"   // ixtiyoriy\n"
            "}\n\n"
            "Javob:\n"
            "{\n"
            "    \"ok\": true,\n"
            "    \"invoice_id\": 12,\n"
            "    \"order_code\": \"ORD-XXXXXXXX\",\n"
            "    \"provider\":  \"payme\",\n"
            "    \"amount\":    \"125000.00\",\n"
            "    \"payment_url\": \"https://checkout.paycom.uz/...\"\n"
            "}"
        ),
    ]

    # ─── 9. Webhook ish jarayoni ────────────────────────────
    story += [
        PageBreak(),
        P("9. To'lov holatlari (status flow)", "h1"),
        kv_table([
            ["Voqea", "Invoice.status", "Order.status"],
            ["Buyurtma yaratildi", "pending", "new"],
            ["Foydalanuvchi to'ladi", "paid (webhook)", "confirmed (avtomatik)"],
            ["Foydalanuvchi bekor qildi yoki to'lov qaytarildi", "cancelled (webhook)", "(o'zgarmaydi)"],
        ]),
        P("Webhook chaqirilganda biz quyidagi mantiqni bajaramiz "
          "(<b>payment/views.py</b> ichida):"),
        code(
            "def _mark_paid(transaction):\n"
            "    invoice = Invoice.objects.select_related('order').get(\n"
            "        id=transaction.account_id\n"
            "    )\n"
            "    invoice.status = Invoice.STATUS_PAID\n"
            "    invoice.save(update_fields=['status', 'updated_at'])\n"
            "    order = invoice.order\n"
            "    if order.status == Order.STATUS_NEW:\n"
            "        order.status = Order.STATUS_CONFIRMED\n"
            "        order.save(update_fields=['status', 'updated_at'])"
        ),
    ]

    # ─── 10. Production checklist ──────────────────────────
    story += [
        P("10. Production'ga chiqarish checklist", "h1"),
        P("• <b>.env</b> da <b>PAYME_TEST_MODE=false</b> va <b>CLICK_TEST_MODE=false</b>", "bullet"),
        P("• <b>.env</b> da merchant kabinetdan olingan haqiqiy (live) kalitlar", "bullet"),
        P("• <b>DJANGO_DEBUG=false</b>", "bullet"),
        P("• <b>SITE_URL</b> haqiqiy domain (https) bo'lishi shart — return URL'lar shu yerdan tortiladi", "bullet"),
        P("• <b>DJANGO_CSRF_TRUSTED_ORIGINS</b> ga haqiqiy domain qo'shing", "bullet"),
        P("• Merchant kabinetda webhook URL'lar publik HTTPS bo'lsin", "bullet"),
        P("• <b>python manage.py migrate</b> production bazasida ham bajarilgan", "bullet"),
        P("• Loglar (LOGGING) yoqilgan va xatolarni kuzatib boring (Sentry yoki shunga o'xshash)", "bullet"),
        Spacer(1, 10),
        Paragraph(
            "Diqqat: webhook endpoint'lariga <b>CSRF</b> tegmaydi (PayTechUZ allaqachon "
            "csrf_exempt qiladi). Lekin to'lov tizimi tomonidan kelgan so'rovlarning "
            "haqiqiyligi kalitlar orqali tekshiriladi — kalitlar maxfiy bo'lsin.",
            S["note"],
        ),
    ]

    # ─── 11. Tezkor sinov ──────────────────────────────────
    story += [
        P("11. Tezkor lokal sinov", "h1"),
        P("Server'ni ishga tushiring:"),
        code("python manage.py runserver"),
        P("Boshqa terminalda webhook'larni publik qiling:"),
        code("ngrok http 8000"),
        P("So'ng saytdan oddiy savat → checkout → Payme/Click tanlash bo'yicha "
          "buyurtma bering. Javobdagi <b>payment_url</b>'ga ergashing va test "
          "kartasi (Payme/Click hujjatlaridagi) bilan to'lov qiling. "
          "Webhook chaqirilgach Invoice <b>paid</b>, Order <b>confirmed</b> "
          "bo'lganini admin'da tekshiring:"),
        code("http://127.0.0.1:8000/admin/payment/invoice/"),
    ]


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="PayTechUZ to'lov tizimini sozlash qo'llanmasi",
        author="Shop project",
    )
    styles = build_styles()
    story = []
    build(story, styles)
    doc.build(story)
    print(f"PDF yaratildi: {OUTPUT}")


if __name__ == "__main__":
    main()
