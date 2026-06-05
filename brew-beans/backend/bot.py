#!/usr/bin/env python3
import json, os, re, uuid, threading, logging, asyncio, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import os
TOKEN = os.environ.get('TELEGRAM_TOKEN', '8527774566:AAGA0bwECbJJCs8xkyf4i934xjHKxlDBP_Q')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5283920277')
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookings.json')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 5000))
BLOCK_HOURS = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('cafe-bot')

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

def load_bookings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_bookings(bookings):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)

def compute_blocked(date_str, bookings=None):
    if bookings is None:
        bookings = load_bookings()
    day = [b for b in bookings if b.get('date') == date_str]
    blocked = set()
    for b in day:
        try:
            h, m = map(int, b['time'].split(':'))
            base = h * 60 + m
            for offset in range(0, BLOCK_HOURS * 60, 30):
                total = base + offset
                bh, bm = divmod(total, 60)
                if bh < 8 or bh >= 22 or (bh == 22 and bm > 0):
                    break
                blocked.add(f'{bh:02d}:{bm:02d}')
        except (ValueError, KeyError):
            continue
    return sorted(blocked)

def format_guests(n):
    if n % 10 == 1 and n % 100 != 11:
        return 'гость'
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return 'гостя'
    return 'гостей'

def send_notification(booking):
    loop = None
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        text = (
            f"\U0001f4e9 <b>Новая бронь</b>\n\n"
            f"\U0001f464 {booking['name']}\n"
            f"\U0001f4de {booking['phone']}\n"
            f"\U0001f4c5 {booking['date']} в {booking['time']}\n"
            f"\U0001f465 {booking['guests']} {format_guests(booking['guests'])}"
        )
        if booking.get('comment'):
            text += f"\n\U0001f4ac {booking['comment']}"
        text += f"\n\n\U0001f194 <code>{booking['id']}</code>"
        loop = asyncio.new_event_loop()
        loop.run_until_complete(bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML'))
    except Exception as e:
        logger.error(f'Notification failed: {e}')
    finally:
        if loop:
            loop.close()

def format_bookings_list(bookings, title):
    if not bookings:
        return f"{title}\n\nНет броней"
    lines = [f"{title} \u2014 {len(bookings)} {format_guests(len(bookings))}", '']
    for b in sorted(bookings, key=lambda x: x['time']):
        extra = f", {b['guests']} чел" if b.get('guests', 2) > 1 else ''
        lines.append(
            f"\U0001f550 {b['time']} \u2014 {b['name']} ({b['phone']}){extra}\n"
            f"\U0001f194 <code>{b['id']}</code>"
        )
    return '\n'.join(lines)

@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'no data'}), 400
    for field in ['name', 'phone', 'date', 'time']:
        if not data.get(field):
            return jsonify({'ok': False, 'error': f'missing {field}'}), 400

    booking = {
        'id': uuid.uuid4().hex[:12],
        'date': data['date'],
        'time': data['time'],
        'name': data['name'],
        'phone': data['phone'],
        'email': data.get('email', ''),
        'guests': int(data.get('guests', 2) or 2),
        'comment': data.get('comment', ''),
        'created_at': datetime.now().isoformat()
    }

    bookings = load_bookings()
    bookings.append(booking)
    save_bookings(bookings)

    threading.Thread(target=send_notification, args=(booking,), daemon=True).start()
    logger.info(f'New booking: {booking["id"]} — {booking["date"]} {booking["time"]} — {booking["name"]}')
    return jsonify({'ok': True, 'id': booking['id']})

@app.route('/api/blocked', methods=['GET'])
def api_blocked():
    date_str = request.args.get('date', '')
    if not date_str:
        return jsonify({'ok': False, 'error': 'missing date'}), 400
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
        return jsonify({'ok': False, 'error': 'invalid date format (expected DD.MM.YYYY)'}), 400
    blocked = compute_blocked(date_str)
    return jsonify({'ok': True, 'date': date_str, 'blocked': blocked})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    save_bookings([])
    logger.info('All bookings reset via API')
    return jsonify({'ok': True})

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton('\U0001f4c5 Сегодня'), KeyboardButton('\U0001f4cb Все брони')],
        [KeyboardButton('\u274c Отменить'), KeyboardButton('\U0001f5d1 Сброс')],
    ]
    await update.message.reply_text(
        '\U0001f44b Добро пожаловать в систему бронирования!\n\n'
        '\U0001f539 /today \u2014 брони на сегодня\n'
        '\U0001f539 /bookings ДД.ММ.ГГГГ \u2014 брони на дату\n'
        '\U0001f539 /cancel ID \u2014 отменить бронь\n'
        '\U0001f539 /reset \u2014 сбросить все брони\n'
        '\U0001f539 /stats \u2014 статистика',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%d.%m.%Y')
    bookings = load_bookings()
    day = [b for b in bookings if b.get('date') == today]
    text = format_bookings_list(day, f'\U0001f4c5 <b>{today}</b>')
    await update.message.reply_text(text, parse_mode='HTML')

async def cmd_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            'Укажите дату: /bookings ДД.ММ.ГГГГ\n'
            'Например: /bookings 15.06.2026'
        )
        return
    date_str = context.args[0]
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
        await update.message.reply_text('Неверный формат. Используйте ДД.ММ.ГГГГ')
        return
    bookings = load_bookings()
    day = [b for b in bookings if b.get('date') == date_str]
    text = format_bookings_list(day, f'\U0001f4c5 <b>{date_str}</b>')
    await update.message.reply_text(text, parse_mode='HTML')

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            'Укажите ID брони: /cancel ID\n'
            'ID можно увидеть в списке броней.'
        )
        return
    booking_id = context.args[0].lower()
    bookings = load_bookings()
    found = [b for b in bookings if b['id'].startswith(booking_id)]
    if not found:
        await update.message.reply_text('\u274c Бронь с таким ID не найдена')
        return
    if len(found) > 1:
        lines = [f'Найдено несколько броней. Уточните ID:']
        for b in found:
            lines.append(f"<code>{b['id']}</code> \u2014 {b['date']} {b['time']} {b['name']}")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')
        return
    booking = found[0]
    keyboard = [[
        InlineKeyboardButton('\u2705 Да, отменить', callback_data=f'cancel_yes_{booking["id"]}'),
        InlineKeyboardButton('\u274c Нет', callback_data='cancel_no')
    ]]
    await update.message.reply_text(
        f'Отменить бронь?\n\n'
        f"\U0001f4c5 {booking['date']} в {booking['time']}\n"
        f"\U0001f464 {booking['name']}\n"
        f"\U0001f4de {booking['phone']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton('\U0001f5d1 Да, сбросить всё', callback_data='reset_yes'),
        InlineKeyboardButton('\u274c Нет', callback_data='reset_no')
    ]]
    await update.message.reply_text(
        '\u26a0\ufe0f <b>Вы уверены?</b>\n\n'
        'Это удалит все брони без возможности восстановления.',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bookings = load_bookings()
    total = len(bookings)
    unique_dates = len(set(b['date'] for b in bookings))
    today = datetime.now().strftime('%d.%m.%Y')
    today_count = len([b for b in bookings if b['date'] == today])
    await update.message.reply_text(
        f'\U0001f4ca <b>Статистика</b>\n\n'
        f'Всего броней: {total}\n'
        f'Дат с бронями: {unique_dates}\n'
        f'Броней сегодня: {today_count}',
        parse_mode='HTML'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel_no':
        await query.edit_message_text('\u274c Отменено')
    elif query.data == 'reset_no':
        await query.edit_message_text('\u274c Сброс отменён')
    elif query.data == 'reset_yes':
        save_bookings([])
        await query.edit_message_text('\u2705 Все брони сброшены')
        logger.info('All bookings reset via bot')
    elif query.data.startswith('cancel_yes_'):
        booking_id = query.data.replace('cancel_yes_', '')
        bookings = load_bookings()
        bookings = [b for b in bookings if b['id'] != booking_id]
        save_bookings(bookings)
        await query.edit_message_text('\u2705 Бронь отменена')
        logger.info(f'Booking {booking_id} cancelled via bot')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == '\U0001f4c5 Сегодня':
        await cmd_today(update, context)
    elif text == '\U0001f4cb Все брони':
        bookings = load_bookings()
        dates = sorted(set(b['date'] for b in bookings), reverse=True)
        now = datetime.now()
        recent = [d for d in dates if d >= (now - timedelta(days=30)).strftime('%d.%m.%Y')][:5]
        if not recent:
            await update.message.reply_text('Нет сохранённых броней')
            return
        keyboard = [[InlineKeyboardButton(d, callback_data=f'date_{d}')] for d in recent]
        await update.message.reply_text(
            'Выберите дату:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif text == '\u274c Отменить':
        await update.message.reply_text(
            'Введите ID брони:\n/cancel ИД\n\n'
            'ID можно посмотреть в списке броней.'
        )
    elif text == '\U0001f5d1 Сброс':
        await cmd_reset(update, context)
    else:
        await update.message.reply_text(
            'Используйте кнопки меню или команды:\n'
            '/today, /bookings, /cancel, /reset, /stats'
        )

async def date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date_str = query.data.replace('date_', '')
    bookings = load_bookings()
    day = [b for b in bookings if b.get('date') == date_str]
    text = format_bookings_list(day, f'\U0001f4c5 <b>{date_str}</b>')
    await query.edit_message_text(text, parse_mode='HTML')

def run_flask():
    logger.info(f'Flask API starting on {HOST}:{PORT}')
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

async def start_bot(bot_app):
    await bot_app.initialize()
    await bot_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await bot_app.start()
    logger.info('Bot started')

async def stop_bot(bot_app):
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()
    logger.info('Bot stopped')

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            bot_app = Application.builder().token(TOKEN).build()
            bot_app.add_handler(CommandHandler('start', cmd_start))
            bot_app.add_handler(CommandHandler('today', cmd_today))
            bot_app.add_handler(CommandHandler('bookings', cmd_bookings))
            bot_app.add_handler(CommandHandler('cancel', cmd_cancel))
            bot_app.add_handler(CommandHandler('reset', cmd_reset))
            bot_app.add_handler(CommandHandler('stats', cmd_stats))
            bot_app.add_handler(CallbackQueryHandler(button_callback, pattern='^(cancel_|reset_)'))
            bot_app.add_handler(CallbackQueryHandler(date_callback, pattern='^date_'))
            bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            loop.run_until_complete(start_bot(bot_app))
            logger.info('Bot connected to Telegram')
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            break
        except Exception as e:
            logger.error(f'Bot connection failed: {e}, retrying in 10s...')
            time.sleep(10)
            continue
        break
    loop.run_until_complete(stop_bot(bot_app))
    loop.close()

def main():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_flask()

if __name__ == '__main__':
    main()
