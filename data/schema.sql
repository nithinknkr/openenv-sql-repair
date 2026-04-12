-- E-commerce Schema
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    name TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK(price > 0),
    stock INTEGER NOT NULL CHECK(stock >= 0)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL CHECK(status IN ('pending', 'shipped', 'delivered', 'cancelled')),
    total_amount DECIMAL(10, 2) NOT NULL CHECK(total_amount >= 0),
    created_at TEXT NOT NULL
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK(unit_price >= 0)
);

-- Realistic e-commerce seed data
INSERT INTO categories (id, name, description) VALUES (1, 'Electronics', 'Smartphones, laptops, audio, and accessories');
INSERT INTO categories (id, name, description) VALUES (2, 'Clothing', 'Men and women apparel, shoes, and accessories');
INSERT INTO categories (id, name, description) VALUES (3, 'Home & Kitchen', 'Appliances, cookware, and home decor');
INSERT INTO categories (id, name, description) VALUES (4, 'Sports & Outdoors', 'Fitness gear, camping, and outdoor recreation');
INSERT INTO categories (id, name, description) VALUES (5, 'Books', 'Fiction, non-fiction, textbooks, and e-books');
INSERT INTO categories (id, name, description) VALUES (6, 'Beauty & Personal Care', 'Skincare, haircare, and wellness products');
INSERT INTO categories (id, name, description) VALUES (7, 'Toys & Games', 'Board games, action figures, and educational toys');
INSERT INTO categories (id, name, description) VALUES (8, 'Automotive', 'Car accessories, tools, and maintenance products');
INSERT INTO categories (id, name, description) VALUES (9, 'Garden & Outdoors', 'Plants, tools, and outdoor furniture');
INSERT INTO categories (id, name, description) VALUES (10, 'Office Supplies', 'Stationery, printers, and desk accessories');

INSERT INTO products (id, category_id, name, price, stock) VALUES (1,  1, 'Sony WH-1000XM5 Wireless Headphones',        349.99, 42);
INSERT INTO products (id, category_id, name, price, stock) VALUES (2,  2, 'Levi''s 501 Original Fit Jeans',              69.99, 128);
INSERT INTO products (id, category_id, name, price, stock) VALUES (3,  3, 'Instant Pot Duo 7-in-1 Pressure Cooker',      99.95,  74);
INSERT INTO products (id, category_id, name, price, stock) VALUES (4,  4, 'Nike Air Zoom Pegasus 40 Running Shoes',      129.99,  56);
INSERT INTO products (id, category_id, name, price, stock) VALUES (5,  5, 'Atomic Habits by James Clear',                16.99, 312);
INSERT INTO products (id, category_id, name, price, stock) VALUES (6,  6, 'CeraVe Moisturizing Cream 19 oz',             18.97, 203);
INSERT INTO products (id, category_id, name, price, stock) VALUES (7,  7, 'LEGO Technic Land Rover Defender',            199.99,  38);
INSERT INTO products (id, category_id, name, price, stock) VALUES (8,  8, 'Armor All Car Interior Detailing Kit',         24.99,  89);
INSERT INTO products (id, category_id, name, price, stock) VALUES (9,  9, 'Fiskars Steel Bypass Pruning Shears',          28.49,  67);
INSERT INTO products (id, category_id, name, price, stock) VALUES (10, 10, 'Moleskine Classic Hardcover Notebook A5',     22.99, 154);
INSERT INTO products (id, category_id, name, price, stock) VALUES (11,  1, 'Samsung 65" QLED 4K Smart TV',              1299.99,  15);
INSERT INTO products (id, category_id, name, price, stock) VALUES (12,  2, 'Patagonia Nano Puff Jacket',                 249.00,  32);
INSERT INTO products (id, category_id, name, price, stock) VALUES (13,  3, 'Dyson V15 Detect Cordless Vacuum',           749.99,  18);
INSERT INTO products (id, category_id, name, price, stock) VALUES (14,  4, 'Hydro Flask 32 oz Wide Mouth Bottle',         44.95, 187);
INSERT INTO products (id, category_id, name, price, stock) VALUES (15,  5, 'Deep Work by Cal Newport',                   14.99, 278);
INSERT INTO products (id, category_id, name, price, stock) VALUES (16,  6, 'Neutrogena Hydro Boost Gel Face Wash',        11.49, 341);
INSERT INTO products (id, category_id, name, price, stock) VALUES (17,  7, 'Hasbro Monopoly Classic Board Game',          24.99,  96);
INSERT INTO products (id, category_id, name, price, stock) VALUES (18,  8, 'DEWALT 20V MAX Cordless Drill Set',           129.00,  43);
INSERT INTO products (id, category_id, name, price, stock) VALUES (19,  9, 'Scotts Turf Builder Lawn Food 15000 sq ft',   54.99,  29);
INSERT INTO products (id, category_id, name, price, stock) VALUES (20, 10, 'HP 63 Black & Tri-Color Ink Cartridges',      34.99, 213);
INSERT INTO products (id, category_id, name, price, stock) VALUES (21,  1, 'Apple AirPods Pro 2nd Generation',           249.00,  67);
INSERT INTO products (id, category_id, name, price, stock) VALUES (22,  2, 'Adidas Ultraboost 22 Running Sneakers',      179.95,  48);
INSERT INTO products (id, category_id, name, price, stock) VALUES (23,  3, 'Lodge 10.25" Cast Iron Skillet',              34.25, 122);
INSERT INTO products (id, category_id, name, price, stock) VALUES (24,  4, 'Manduka PRO Yoga Mat 6mm',                   120.00,  35);
INSERT INTO products (id, category_id, name, price, stock) VALUES (25,  5, 'Sapiens by Yuval Noah Harari',                18.00, 196);
INSERT INTO products (id, category_id, name, price, stock) VALUES (26,  6, 'Olaplex No.3 Hair Perfector 100ml',           30.00, 147);
INSERT INTO products (id, category_id, name, price, stock) VALUES (27,  7, 'Rubik''s Cube 3x3 Speed Cube',               12.99, 234);
INSERT INTO products (id, category_id, name, price, stock) VALUES (28,  8, 'Thule Force XT Rooftop Cargo Box',           549.95,  12);
INSERT INTO products (id, category_id, name, price, stock) VALUES (29,  9, 'AeroGarden Harvest Indoor Garden',            99.95,  51);
INSERT INTO products (id, category_id, name, price, stock) VALUES (30, 10, 'Scotch Heavy Duty Shipping Tape 6-Pack',      12.49, 389);
INSERT INTO products (id, category_id, name, price, stock) VALUES (31,  1, 'Logitech MX Master 3S Wireless Mouse',        99.99,  83);
INSERT INTO products (id, category_id, name, price, stock) VALUES (32,  2, 'Nike Dri-FIT Training T-Shirt',               34.99, 267);
INSERT INTO products (id, category_id, name, price, stock) VALUES (33,  3, 'Nespresso Vertuo Next Coffee Machine',        179.00,  29);
INSERT INTO products (id, category_id, name, price, stock) VALUES (34,  4, 'TRX All-in-One Suspension Trainer',           199.95,  24);
INSERT INTO products (id, category_id, name, price, stock) VALUES (35,  5, 'Python Crash Course 3rd Edition',              35.99, 143);
INSERT INTO products (id, category_id, name, price, stock) VALUES (36,  6, 'Maybelline Fit Me Matte Foundation',            9.99, 412);
INSERT INTO products (id, category_id, name, price, stock) VALUES (37,  7, 'Melissa & Doug Wooden Blocks Set',             29.99,  78);
INSERT INTO products (id, category_id, name, price, stock) VALUES (38,  8, 'Chemical Guys Car Wash Soap Concentrate',      17.99, 156);
INSERT INTO products (id, category_id, name, price, stock) VALUES (39,  9, 'Miracle-Gro All Purpose Plant Food',           16.99,  94);
INSERT INTO products (id, category_id, name, price, stock) VALUES (40, 10, 'APC Back-UPS 600VA Battery Backup',            64.99,  37);

-- Users 1-25 have placed orders. Users 26-50 are registered but have never ordered.
-- This split is critical for the logic_wrong_join task (LEFT JOIN must show NULLs for users 26-50).
INSERT INTO users (id, username, email, created_at) VALUES (1,  'james_wilson',     'james.wilson@gmail.com',      '2024-03-15 09:22:14');
INSERT INTO users (id, username, email, created_at) VALUES (2,  'sarah_chen',        'sarah.chen@outlook.com',      '2024-04-02 14:35:07');
INSERT INTO users (id, username, email, created_at) VALUES (3,  'priya_nair',        'priya.nair@yahoo.com',        '2024-04-19 11:08:43');
INSERT INTO users (id, username, email, created_at) VALUES (4,  'carlos_mendoza',    'c.mendoza@hotmail.com',       '2024-05-07 16:52:30');
INSERT INTO users (id, username, email, created_at) VALUES (5,  'emily_hartford',    'emily.h@gmail.com',           '2024-05-23 08:17:55');
INSERT INTO users (id, username, email, created_at) VALUES (6,  'raj_patel',         'rajpatel88@gmail.com',        '2024-06-11 20:44:12');
INSERT INTO users (id, username, email, created_at) VALUES (7,  'olivia_brooks',     'o.brooks@icloud.com',         '2024-07-03 13:29:38');
INSERT INTO users (id, username, email, created_at) VALUES (8,  'michael_osei',      'm.osei@protonmail.com',       '2024-07-28 07:51:22');
INSERT INTO users (id, username, email, created_at) VALUES (9,  'aisha_malik',       'aisha.malik@gmail.com',       '2024-08-14 19:03:47');
INSERT INTO users (id, username, email, created_at) VALUES (10, 'noah_fischer',      'noah.fischer@web.de',         '2024-09-01 10:16:59');
INSERT INTO users (id, username, email, created_at) VALUES (11, 'liu_yang',          'liu.yang@163.com',            '2024-09-18 15:42:33');
INSERT INTO users (id, username, email, created_at) VALUES (12, 'isabella_russo',    'i.russo@libero.it',           '2024-10-05 12:28:16');
INSERT INTO users (id, username, email, created_at) VALUES (13, 'kwame_asante',      'k.asante@gmail.com',          '2024-10-22 09:55:44');
INSERT INTO users (id, username, email, created_at) VALUES (14, 'anna_kowalski',     'anna.kowalski@wp.pl',         '2024-11-08 17:39:21');
INSERT INTO users (id, username, email, created_at) VALUES (15, 'daniel_levine',     'd.levine@gmail.com',          '2024-11-25 06:14:52');
INSERT INTO users (id, username, email, created_at) VALUES (16, 'fatima_al_rashid',  'f.alrashid@hotmail.com',      '2024-12-12 21:07:38');
INSERT INTO users (id, username, email, created_at) VALUES (17, 'tom_nakamura',      't.nakamura@docomo.ne.jp',     '2024-12-28 14:53:09');
INSERT INTO users (id, username, email, created_at) VALUES (18, 'grace_kim',         'grace.kim@kakao.com',         '2025-01-04 08:31:47');
INSERT INTO users (id, username, email, created_at) VALUES (19, 'omar_hassan',       'omar.hassan@gmail.com',       '2025-01-11 16:20:14');
INSERT INTO users (id, username, email, created_at) VALUES (20, 'elena_popescu',     'e.popescu@yahoo.ro',          '2025-01-18 11:45:28');
INSERT INTO users (id, username, email, created_at) VALUES (21, 'marcus_johnson',    'marcus.j@gmail.com',          '2024-03-22 13:17:05');
INSERT INTO users (id, username, email, created_at) VALUES (22, 'yuki_tanaka',       'yuki.tanaka@gmail.com',       '2024-04-09 09:44:31');
INSERT INTO users (id, username, email, created_at) VALUES (23, 'amara_diallo',      'amara.diallo@gmail.com',      '2024-04-27 19:22:58');
INSERT INTO users (id, username, email, created_at) VALUES (24, 'lucas_schmidt',     'l.schmidt@gmx.de',            '2024-05-14 07:58:42');
INSERT INTO users (id, username, email, created_at) VALUES (25, 'chloe_martin',      'chloe.martin@orange.fr',      '2024-06-01 15:36:19');
INSERT INTO users (id, username, email, created_at) VALUES (26, 'dmitri_volkov',     'd.volkov@mail.ru',            '2024-06-18 10:23:07');
INSERT INTO users (id, username, email, created_at) VALUES (27, 'nina_bergstrom',    'nina.b@hotmail.se',           '2024-07-05 18:41:53');
INSERT INTO users (id, username, email, created_at) VALUES (28, 'alex_okonkwo',      'a.okonkwo@gmail.com',         '2024-07-22 12:09:36');
INSERT INTO users (id, username, email, created_at) VALUES (29, 'sofia_gonzalez',    'sofia.g@gmail.com',           '2024-08-08 08:47:21');
INSERT INTO users (id, username, email, created_at) VALUES (30, 'ryan_obrien',       'ryan.obrien@eircom.net',      '2024-08-25 16:34:58');
INSERT INTO users (id, username, email, created_at) VALUES (31, 'mei_lin',           'mei.lin@qq.com',              '2024-09-11 11:02:43');
INSERT INTO users (id, username, email, created_at) VALUES (32, 'hassan_ibrahim',    'h.ibrahim@gmail.com',         '2024-09-28 20:15:26');
INSERT INTO users (id, username, email, created_at) VALUES (33, 'victoria_santos',   'v.santos@gmail.com',          '2024-10-15 07:29:11');
INSERT INTO users (id, username, email, created_at) VALUES (34, 'pierre_dubois',     'p.dubois@gmail.com',          '2024-11-01 15:56:47');
INSERT INTO users (id, username, email, created_at) VALUES (35, 'nadia_petrov',      'nadia.petrov@yandex.ru',      '2024-11-18 09:44:32');
INSERT INTO users (id, username, email, created_at) VALUES (36, 'jake_thompson',     'jake.t@gmail.com',            '2024-12-05 14:23:18');
INSERT INTO users (id, username, email, created_at) VALUES (37, 'amelia_ward',       'amelia.ward@outlook.com',     '2024-12-22 08:11:55');
INSERT INTO users (id, username, email, created_at) VALUES (38, 'samuel_adeyemi',    's.adeyemi@yahoo.com',         '2025-01-08 18:39:41');
INSERT INTO users (id, username, email, created_at) VALUES (39, 'layla_hassan',      'layla.h@gmail.com',           '2025-01-15 12:28:26');
INSERT INTO users (id, username, email, created_at) VALUES (40, 'andrei_ionescu',    'a.ionescu@gmail.com',         '2025-01-22 07:17:13');
INSERT INTO users (id, username, email, created_at) VALUES (41, 'jessica_lee',       'jess.lee@gmail.com',          '2024-03-30 16:55:08');
INSERT INTO users (id, username, email, created_at) VALUES (42, 'ben_cohen',         'b.cohen@gmail.com',           '2024-04-16 10:33:44');
INSERT INTO users (id, username, email, created_at) VALUES (43, 'zara_ahmed',        'zara.ahmed@outlook.com',      '2024-05-03 19:22:21');
INSERT INTO users (id, username, email, created_at) VALUES (44, 'luca_ferrari',      'l.ferrari@gmail.com',         '2024-05-20 08:10:58');
INSERT INTO users (id, username, email, created_at) VALUES (45, 'diana_chen',        'diana.chen88@gmail.com',      '2024-06-06 13:49:35');
INSERT INTO users (id, username, email, created_at) VALUES (46, 'kevin_brown',       'kevin.brown@yahoo.com',       '2024-06-23 17:38:22');
INSERT INTO users (id, username, email, created_at) VALUES (47, 'hannah_muller',     'h.muller@t-online.de',        '2024-07-10 09:27:09');
INSERT INTO users (id, username, email, created_at) VALUES (48, 'ibrahim_al_farsi',  'i.alfarsi@gmail.com',         '2024-07-27 21:15:56');
INSERT INTO users (id, username, email, created_at) VALUES (49, 'clara_beaumont',    'c.beaumont@gmail.com',        '2024-08-13 11:04:43');
INSERT INTO users (id, username, email, created_at) VALUES (50, 'yusuf_ozturk',      'y.ozturk@gmail.com',          '2024-08-30 15:53:30');

-- Orders: only users 1-25 have placed orders (26-50 appear as NULL in LEFT JOIN tasks)
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (1,  3,  'delivered', 366.98, '2025-01-05 14:22:09');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (2,  7,  'shipped',    69.99, '2025-01-08 10:15:33');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (3,  1,  'pending',  1299.99, '2025-01-12 18:44:21');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (4,  12, 'delivered',  49.43, '2025-01-15 09:07:55');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (5,  5,  'cancelled',  16.99, '2025-01-18 12:31:44');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (6,  9,  'delivered', 174.94, '2025-01-21 16:58:30');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (7,  2,  'shipped',    99.95, '2025-01-24 08:22:17');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (8,  18, 'pending',   795.97, '2025-01-27 20:11:08');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (9,  4,  'delivered',  82.97, '2025-02-01 11:45:52');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (10, 22, 'cancelled',  24.99, '2025-02-04 07:33:19');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (11, 6,  'delivered', 348.99, '2025-02-07 14:18:03');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (12, 14, 'delivered', 120.00, '2025-02-10 09:52:37');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (13, 10, 'shipped',    68.98, '2025-02-13 17:06:22');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (14, 16, 'pending',    89.97, '2025-02-16 11:29:54');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (15, 23, 'delivered', 199.99, '2025-02-19 08:44:11');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (16, 8,  'cancelled', 129.00, '2025-02-22 19:33:48');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (17, 13, 'delivered', 134.20, '2025-02-25 13:17:35');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (18, 19, 'shipped',   199.95, '2025-02-28 07:55:19');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (19, 11, 'delivered', 107.45, '2025-03-03 16:42:07');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (20, 24, 'pending',   549.95, '2025-03-06 10:28:43');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (21, 15, 'shipped',   201.99, '2025-03-09 14:51:26');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (22, 20, 'delivered',  54.98, '2025-03-12 09:16:54');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (23, 17, 'delivered', 179.95, '2025-03-15 18:07:33');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (24, 25, 'cancelled', 154.94, '2025-03-18 12:39:18');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (25, 21, 'pending',  1364.98, '2025-03-21 08:23:47');

-- Order items: multiple items per order (realistic shopping cart behavior)
-- Order 1: Sony Headphones + Atomic Habits
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (1,  1,  1,  1, 349.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (2,  1,  5,  1,  16.99);
-- Order 2: Levi's Jeans
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (3,  2,  2,  1,  69.99);
-- Order 3: Samsung TV
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (4,  3,  11, 1, 1299.99);
-- Order 4: CeraVe x2 + Neutrogena
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (5,  4,  6,  2,  18.97);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (6,  4,  16, 1,  11.49);
-- Order 5: Atomic Habits
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (7,  5,  5,  1,  16.99);
-- Order 6: Nike Shoes + Hydro Flask
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (8,  6,  4,  1, 129.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (9,  6,  14, 1,  44.95);
-- Order 7: Instant Pot
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (10, 7,  3,  1,  99.95);
-- Order 8: Dyson Vacuum + Moleskine x2
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (11, 8,  13, 1, 749.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (12, 8,  10, 2,  22.99);
-- Order 9: Nike T-Shirt x2 + Rubik's Cube
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (13, 9,  32, 2,  34.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (14, 9,  27, 1,  12.99);
-- Order 10: Armor All Kit
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (15, 10, 8,  1,  24.99);
-- Order 11: AirPods Pro + Logitech Mouse
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (16, 11, 21, 1, 249.00);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (17, 11, 31, 1,  99.99);
-- Order 12: Yoga Mat
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (18, 12, 24, 1, 120.00);
-- Order 13: Python Book + Deep Work + Sapiens
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (19, 13, 35, 1,  35.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (20, 13, 15, 1,  14.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (21, 13, 25, 1,  18.00);
-- Order 14: Olaplex x2 + Maybelline x3
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (22, 14, 26, 2,  30.00);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (23, 14, 36, 3,   9.99);
-- Order 15: LEGO Set
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (24, 15, 7,  1, 199.99);
-- Order 16: DEWALT Drill
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (25, 16, 18, 1, 129.00);
-- Order 17: Instant Pot + Cast Iron Skillet
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (26, 17, 3,  1,  99.95);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (27, 17, 23, 1,  34.25);
-- Order 18: TRX Trainer
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (28, 18, 34, 1, 199.95);
-- Order 19: HP Ink x2 + Scotch Tape x3
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (29, 19, 20, 2,  34.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (30, 19, 30, 3,  12.49);
-- Order 20: Thule Cargo Box
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (31, 20, 28, 1, 549.95);
-- Order 21: Nespresso + Moleskine
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (32, 21, 33, 1, 179.00);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (33, 21, 10, 1,  22.99);
-- Order 22: Monopoly + Melissa & Doug Blocks
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (34, 22, 17, 1,  24.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (35, 22, 37, 1,  29.99);
-- Order 23: Adidas Ultraboost
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (36, 23, 22, 1, 179.95);
-- Order 24: Scotts Lawn Food + AeroGarden
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (37, 24, 19, 1,  54.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (38, 24, 29, 1,  99.95);
-- Order 25: Samsung TV + APC Battery Backup
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (39, 25, 11, 1, 1299.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (40, 25, 40, 1,   64.99);

-- Additional orders to test having > 1
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (26, 1, 'delivered', 150.00, '2025-03-25 10:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (27, 2, 'pending', 75.00, '2025-03-26 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (28, 3, 'shipped', 200.00, '2025-03-27 12:00:00');
