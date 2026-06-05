-- База данных кофейни Brew & Beans

CREATE TABLE IF NOT EXISTS coffees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    origin VARCHAR(100),
    roast_level VARCHAR(20) CHECK (roast_level IN ('light', 'medium', 'dark')),
    price_grams NUMERIC(6,2),           -- цена за 100г в рублях
    in_stock BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    coffee_id INT REFERENCES coffees(id),
    name VARCHAR(100) NOT NULL,
    method VARCHAR(30) NOT NULL,        -- espresso, v60, chemex, aeropress...
    recipe_json JSONB,                  -- {water: 250, coffee: 15, temp: 92}
    price_cup NUMERIC(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    guest_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    booked_at TIMESTAMP DEFAULT now(),
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    guests INT DEFAULT 2,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','confirmed','cancelled'))
);

CREATE TABLE IF NOT EXISTS barista_ratings (
    id SERIAL PRIMARY KEY,
    barista VARCHAR(100) NOT NULL,
    recipe_id INT REFERENCES recipes(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Данные
INSERT INTO coffees (name, origin, roast_level, price_grams) VALUES
  ('Эфиопия Йиргачеффе', 'Эфиопия', 'light',  120.00),
  ('Кения АБ',           'Кения',   'medium', 135.00),
  ('Колумбия Уила',      'Колумбия','medium', 110.00),
  ('Бразилия Сантос',    'Бразилия','dark',    95.00);

INSERT INTO recipes (coffee_id, name, method, recipe_json, price_cup) VALUES
  (1, 'V60 Эфиопия',         'v60',    '{"water":250,"coffee":15,"temp":92}',  490),
  (1, 'Аэропресс Эфиопия',   'aeropress','{"water":200,"coffee":18,"temp":88}', 450),
  (2, 'Chemex Кения',        'chemex', '{"water":300,"coffee":20,"temp":90}',  520),
  (3, 'Эспрессо Колумбия',   'espresso','{"water":40,"coffee":18,"temp":93}',  350),
  (4, 'Фильтр Бразилия',     'filter',  '{"water":240,"coffee":16,"temp":85}',  380);

INSERT INTO bookings (guest_name, phone, visit_date, visit_time, guests, status) VALUES
  ('Анна', '+7-999-111-22-33', now()::date + 1, '10:00', 2, 'confirmed'),
  ('Иван', '+7-999-444-55-66', now()::date + 1, '14:00', 4, 'confirmed'),
  ('Мария','+7-999-777-88-99', now()::date + 2, '11:30', 3, 'pending');

INSERT INTO barista_ratings (barista, recipe_id, rating, comment) VALUES
  ('Алексей', 1, 5, 'Идеально раскрыл цитрус'),
  ('Алексей', 3, 4, 'Хорошо, но можно ярче'),
  ('Мария',   2, 5, 'Лучший аэропресс в городе'),
  ('Мария',   4, 3, 'Передержала эспрессо');

-- Запросы
\echo '=== Меню с ценами ==='
SELECT r.name, c.origin, r.method, r.price_cup
FROM recipes r JOIN coffees c ON c.id = r.coffee_id
ORDER BY r.price_cup DESC;

\echo '=== Средняя оценка бариста ==='
SELECT barista, round(avg(rating), 2) AS avg_rating, count(*) AS оценок
FROM barista_ratings
GROUP BY barista
ORDER BY avg_rating DESC;

\echo '=== Брони на завтра ==='
SELECT guest_name, visit_time, guests, status
FROM bookings
WHERE visit_date = now()::date + 1
ORDER BY visit_time;

\echo '=== Какой метод заваривания популярнее всего ==='
SELECT r.method, count(br.id) AS отзывов, round(avg(br.rating), 2) AS средняя_оценка
FROM barista_ratings br JOIN recipes r ON r.id = br.recipe_id
GROUP BY r.method
ORDER BY отзывов DESC;

\echo '=== Кофе, который сейчас нет в наличии ==='
SELECT name, origin FROM coffees WHERE NOT in_stock;
