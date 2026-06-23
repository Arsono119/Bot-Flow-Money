import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from database import init_db, save_transaction, get_summary, get_recent_transactions, get_category_summary
from ai_handler import parse_transaction, format_rupiah

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "ISI_TOKEN_BOT_KAMU")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "ISI_GROQ_API_KEY_KAMU")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

EMOJI = {"income": "💰", "expense": "💸"}


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Halo! Aku bakal catetin pemasukan & pengeluaran kamu ✨\n\n"
        "Caranya gampang, tinggal chat aja kayak gini:\n"
        "• \"beli nasi goreng 25rb\"\n"
        "• \"gajian 5jt\"\n"
        "• \"naik grab 15rb\"\n"
        "• \"jualan laku 200rb\"\n\n"
        "Perintah:\n"
        "/summary — liat rekap\n"
        "/recent — transaksi terakhir\n"
        "/categories — pengeluaran per kategori bulan ini\n"
        "/help — bantuan"
    )


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📌 Cara Pakai:\n\n"
        "Tinggal chat aja langsung, misal:\n"
        "• \"beli kopi 20rb\" → otomatis dicatet sebagai pengeluaran\n"
        "• \"gajian 5jt\" → dicatet sebagai pemasukan\n\n"
        "Perintah:\n"
        "/summary — rekap saldo\n"
        "/recent — 5 transaksi terakhir\n"
        "/categories — liat pengeluaran per kategori bulan ini\n"
        "/help — ini"
    )


async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    result = parse_transaction(text)
    if result is None:
        await update.message.reply_text(
            "Maaf ya, aku kurang paham 😅\n"
            "Coba kasih tau yang lebih jelas, misal: \"beli kopi 25rb\""
        )
        return

    save_transaction(
        user_id=user_id,
        ttype=result["type"],
        amount=result["amount"],
        category=result["category"],
        note=text,
    )

    emoji = EMOJI[result["type"]]
    label = "Pemasukan" if result["type"] == "income" else "Pengeluaran"
    await update.message.reply_text(
        f"{emoji} *{label}*: {format_rupiah(result['amount'])}\n"
        f"📂 Kategori: {result['category']}\n"
        f"✅ Udah dicatet ya!",
        parse_mode="Markdown",
    )


async def summary(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    args = context.args
    period = "all"
    if args:
        p = args[0].lower()
        if p in ("day", "today", "hari"):
            period = "day"
        elif p in ("week", "minggu"):
            period = "week"
        elif p in ("month", "bulan"):
            period = "month"

    data = get_summary(user_id, period)

    label_map = {"day": "Hari ini", "week": "7 hari terakhir", "month": "Bulan ini", "all": "Semua waktu"}
    label = label_map.get(period, "Semua waktu")

    await update.message.reply_text(
        f"📊 *Rekap Keuangan — {label}*\n\n"
        f"{EMOJI['income']} Pemasukan: *{format_rupiah(data['total_income'])}*\n"
        f"{EMOJI['expense']} Pengeluaran: *{format_rupiah(data['total_expense'])}*\n"
        f"⚖️ Saldo: *{format_rupiah(data['balance'])}*",
        parse_mode="Markdown",
    )


async def recent(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    transactions = get_recent_transactions(user_id)

    if not transactions:
        await update.message.reply_text("Belum ada transaksi nih, yuk catet dulu!")
        return

    lines = ["📋 *5 Transaksi Terakhir:*\n"]
    for t in transactions:
        emoji = EMOJI[t["type"]]
        label = "Pemasukan" if t["type"] == "income" else "Pengeluaran"
        lines.append(
            f"{emoji} {label} — {format_rupiah(t['amount'])} ({t['category']})"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def categories(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cats = get_category_summary(user_id)

    if not cats:
        await update.message.reply_text(
            "Belum ada pengeluaran bulan ini. Hemat banget sih! 🏆"
        )
        return

    total = sum(c["total"] for c in cats)
    lines = ["📂 *Pengeluaran Bulan Ini per Kategori:*\n"]
    for c in cats:
        pct = (c["total"] / total) * 100 if total > 0 else 0
        lines.append(f"• {c['category']}: {format_rupiah(c['total'])} ({pct:.0f}%)")
    lines.append(f"\nTotal: *{format_rupiah(total)}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


def main():
    init_db()
    logger.info("Database siap!")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot jalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
