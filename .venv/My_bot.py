import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Telegram bot tokenini kiriting
TOKEN = '7500832362:AAFDCipQ7Pkpl6daVeNlwkO1Q4HRcU_slRs'

# Valyuta kursini olish uchun URL
EXCHANGE_API_URL = 'https://api.exchangerate-api.com/v4/latest/USD'

# Loglarni yozish
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# /start komandasi
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Valyutani tanlash", callback_data='choose_currency')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Salom! Men sizga valyuta kurslarini hisoblashda yordam bera olaman. '
                                    'Valyuta kursini hisoblash uchun kerakli valyutalarni tanlang:',
                                    reply_markup=reply_markup)


# Foydalanuvchi valyutani tanlashi
async def choose_currency(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("USD to UZS", callback_data='USD_UZS')],
        [InlineKeyboardButton("EUR to UZS", callback_data='EUR_UZS')],
        [InlineKeyboardButton("USD to EUR", callback_data='USD_EUR')],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text('Valyuta tanlang:', reply_markup=reply_markup)


# Foydalanuvchi orqaga qaytish tugmasini bosganda
async def go_back(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Valyutani tanlash", callback_data='choose_currency')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text('Salom! Men sizga valyuta kurslarini hisoblashda yordam bera olaman. '
                                                  'Valyuta kursini hisoblash uchun kerakli valyutalarni tanlang:',
                                                  reply_markup=reply_markup)


# Valyuta kurslarini olish
async def get_exchange_rate(update: Update, context: CallbackContext) -> None:
    try:
        # Kursni olish
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()

        # Foydalanuvchi tanlagan valyutani aniqlash
        query = update.callback_query
        await query.answer()

        from_currency, to_currency = query.data.split('_')

        # Kursni hisoblash
        if from_currency in data['rates'] and to_currency in data['rates']:
            rate = data['rates'][to_currency] / data['rates'][from_currency]
            await query.edit_message_text(f'{from_currency} dan {to_currency} ga kurs: {rate:.2f}. '
                                          'Endi miqdorni kiriting, masalan: "100 USD".\n\n'
                                          'Yana boshqa valyutalarni ko\'rish uchun "Orqaga" tugmasini bosing.',
                                          reply_markup=InlineKeyboardMarkup([
                                              [InlineKeyboardButton("Orqaga", callback_data='choose_currency')]
                                          ]))
            # Keyingi qadamni kutamiz
            context.user_data['from_currency'] = from_currency
            context.user_data['to_currency'] = to_currency
        else:
            await query.edit_message_text(
                'Kursni topishda xatolik yuz berdi. Iltimos, valyuta nomlarini tekshirib ko\'ring.')

    except Exception as e:
        await update.message.reply_text(f'Xatolik yuz berdi: {e}')


# Foydalanuvchidan miqdor kiritishni kutish
async def process_amount(update: Update, context: CallbackContext) -> None:
    try:
        amount = float(update.message.text.split()[0])  # Faqat raqamni olish
        from_currency = context.user_data['from_currency']
        to_currency = context.user_data['to_currency']

        # Kursni olish
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()

        # Kursni hisoblash
        if from_currency in data['rates'] and to_currency in data['rates']:
            rate = data['rates'][to_currency] / data['rates'][from_currency]
            result = amount * rate
            await update.message.reply_text(f'{amount} {from_currency} = {result:.2f} {to_currency}\n\n'
                                            'Yana boshqa valyutalarni ko\'rish uchun "Orqaga" tugmasini bosing.',
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton("Orqaga", callback_data='choose_currency')]
                                            ]))
        else:
            await update.message.reply_text('Kursni topishda xatolik yuz berdi. Iltimos, valyutani tekshirib ko\'ring.')
    except ValueError:
        await update.message.reply_text('Iltimos, faqat raqamli miqdorni kiriting, masalan: "100 USD".')
    except Exception as e:
        await update.message.reply_text(f'Xatolik yuz berdi: {e}')


# Main funksiya
def main():
    # Botni ishga tushurish
    application = Application.builder().token(TOKEN).build()

    # /start, /kurs komandalarini bog'lash
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(choose_currency, pattern='choose_currency'))
    application.add_handler(CallbackQueryHandler(get_exchange_rate))
    application.add_handler(CallbackQueryHandler(go_back, pattern='go_back'))

    # Foydalanuvchidan miqdor so'rash
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount))

    # Botni ishga tushurish
    application.run_polling()


if __name__ == '__main__':
    main()
