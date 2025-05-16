from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import PeerIdInvalidError
import asyncio

# الحالات
TARGET_USER, MESSAGE, COUNT, ADD_MORE = range(4)

# بيانات حسابك الشخصي
api_id = 27035167
api_hash = "b45e54c91eb8fe4a567ddbb83b6c71db"
session_string = "1BJWap1wBu5vwHD6gj3nwEwjlkSdxEax3PF1hDT_xcdrLnK7sJNt8cWMRR8CzJCOnyCDgcVuKOhH0lC2bx-uMxsCfy3vru56OvJt3ijqwe-KOLd7xlJS6fvvm1Lc2tuHTCYOXhWf0QJryEMoFiX3DspuYYWrAknksLbP8QD5Mea-CFAe9tafXHiN9f9pix5mKMClSwnSjuV47e2ZBDLe8WscOezh_CyrW3G02uzVsh49MyEPRAjMaPLnBH-Z4jikwQzF0GIqTPUL79bY3WvnSEwJcLKNhhRTSLLF6_OwV-lbyRxvZoGWf5NjWOkEoR3Ad1g5dFndj1Yq2Zi3VU7JYzDI8TazVZ1Q="

# إنشاء عميل Telethon ثابت
client = TelegramClient(StringSession(session_string), api_id, api_hash)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['messages'] = []
    await update.message.reply_text("أدخل اليوزر نيم أو ID للشخص المستهدف:", reply_markup=ReplyKeyboardRemove())
    return TARGET_USER

async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_user'] = update.message.text.strip().replace("@", "")
    await update.message.reply_text("أدخل الرسالة الأولى:")
    return MESSAGE

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['messages'].append(update.message.text)
    reply_keyboard = [["نعم"], ["لا"]]
    await update.message.reply_text(
        "هل تريد إضافة رسالة أخرى؟",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ADD_MORE

async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() == "نعم":
        await update.message.reply_text("أدخل الرسالة التالية:", reply_markup=ReplyKeyboardRemove())
        return MESSAGE
    else:
        await update.message.reply_text("كم مرة تريد إرسال الرسائل؟", reply_markup=ReplyKeyboardRemove())
        return COUNT

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(update.message.text)
    context.user_data['count'] = count

    try:
        await client.start()
        entity = await client.get_entity(context.user_data['target_user'])

        for i in range(count):
            try:
                msg = context.user_data['messages'][i % len(context.user_data['messages'])]
                await client.send_message(entity, msg)
                await asyncio.sleep(0.5)  # لتجنب الحظر المؤقت
            except PeerIdInvalidError:
                await update.message.reply_text("فشل الإرسال: الـ ID أو اليوزر غير صالح")
                break
            except Exception as e:
                await update.message.reply_text(f"فشل الإرسال: {e}")
                break

    except Exception as e:
        await update.message.reply_text(f"فشل الاتصال بالحساب: {e}")
    finally:
        await client.disconnect()

    await update.message.reply_text("تم التنفيذ. أرسل اليوزر التالي مباشرة للبدء من جديد.")
    return TARGET_USER

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token("7087728389:AAGh7gJHzyXJavClc6WWPG2C8FV7yRU5uEQ").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TARGET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_user)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
            ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    from flask import Flask
    from threading import Thread

    web_app = Flask(__name__)

    @web_app.route('/')
    def home():
        return "Bot is running!"

    def run():
        web_app.run(host='0.0.0.0', port=8080)

    Thread(target=run).start()
    app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())