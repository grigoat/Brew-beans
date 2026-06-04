# Brew & Beans — Спешелти кофейня

Два сайта + бэкенд с Telegram-уведомлениями.

## Структура

```
backend/      — Flask API + Telegram Bot
landing/      — Одностраничный сайт (index.html)
multipage/    — Многостраничный сайт (5 страниц)
```

## Деплой

### 1. Бэкенд (Render.com)
1. Создайте аккаунт на render.com
2. New → Web Service → Connect GitHub repo
3. Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Free план — готово

### 2. Фронтенды (Netlify / GitHub Pages)
- **landing/** — перетащите папку на Netlify
- **multipage/** — перетащите папку на Netlify

### 3. Обновите BACKEND_URL
В файлах `landing/index.html` и `multipage/contact.html`
замените `http://localhost:5000` на ваш Render URL
(например `https://cafe-bot.onrender.com`)
