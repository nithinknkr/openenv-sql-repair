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

-- Hardcoded INSERTS
INSERT INTO categories (id, name, description) VALUES (1, 'Category 1', 'Description for category 1');
INSERT INTO categories (id, name, description) VALUES (2, 'Category 2', 'Description for category 2');
INSERT INTO categories (id, name, description) VALUES (3, 'Category 3', 'Description for category 3');
INSERT INTO categories (id, name, description) VALUES (4, 'Category 4', 'Description for category 4');
INSERT INTO categories (id, name, description) VALUES (5, 'Category 5', 'Description for category 5');
INSERT INTO categories (id, name, description) VALUES (6, 'Category 6', 'Description for category 6');
INSERT INTO categories (id, name, description) VALUES (7, 'Category 7', 'Description for category 7');
INSERT INTO categories (id, name, description) VALUES (8, 'Category 8', 'Description for category 8');
INSERT INTO categories (id, name, description) VALUES (9, 'Category 9', 'Description for category 9');
INSERT INTO categories (id, name, description) VALUES (10, 'Category 10', 'Description for category 10');
INSERT INTO products (id, category_id, name, price, stock) VALUES (1, 1, 'Product 1', 12.5, 99);
INSERT INTO products (id, category_id, name, price, stock) VALUES (2, 2, 'Product 2', 15.0, 98);
INSERT INTO products (id, category_id, name, price, stock) VALUES (3, 3, 'Product 3', 17.5, 97);
INSERT INTO products (id, category_id, name, price, stock) VALUES (4, 4, 'Product 4', 20.0, 96);
INSERT INTO products (id, category_id, name, price, stock) VALUES (5, 5, 'Product 5', 22.5, 95);
INSERT INTO products (id, category_id, name, price, stock) VALUES (6, 6, 'Product 6', 25.0, 94);
INSERT INTO products (id, category_id, name, price, stock) VALUES (7, 7, 'Product 7', 27.5, 93);
INSERT INTO products (id, category_id, name, price, stock) VALUES (8, 8, 'Product 8', 30.0, 92);
INSERT INTO products (id, category_id, name, price, stock) VALUES (9, 9, 'Product 9', 32.5, 91);
INSERT INTO products (id, category_id, name, price, stock) VALUES (10, 10, 'Product 10', 35.0, 90);
INSERT INTO products (id, category_id, name, price, stock) VALUES (11, 1, 'Product 11', 37.5, 89);
INSERT INTO products (id, category_id, name, price, stock) VALUES (12, 2, 'Product 12', 40.0, 88);
INSERT INTO products (id, category_id, name, price, stock) VALUES (13, 3, 'Product 13', 42.5, 87);
INSERT INTO products (id, category_id, name, price, stock) VALUES (14, 4, 'Product 14', 45.0, 86);
INSERT INTO products (id, category_id, name, price, stock) VALUES (15, 5, 'Product 15', 47.5, 85);
INSERT INTO products (id, category_id, name, price, stock) VALUES (16, 6, 'Product 16', 50.0, 84);
INSERT INTO products (id, category_id, name, price, stock) VALUES (17, 7, 'Product 17', 52.5, 83);
INSERT INTO products (id, category_id, name, price, stock) VALUES (18, 8, 'Product 18', 55.0, 82);
INSERT INTO products (id, category_id, name, price, stock) VALUES (19, 9, 'Product 19', 57.5, 81);
INSERT INTO products (id, category_id, name, price, stock) VALUES (20, 10, 'Product 20', 60.0, 80);
INSERT INTO products (id, category_id, name, price, stock) VALUES (21, 1, 'Product 21', 62.5, 79);
INSERT INTO products (id, category_id, name, price, stock) VALUES (22, 2, 'Product 22', 65.0, 78);
INSERT INTO products (id, category_id, name, price, stock) VALUES (23, 3, 'Product 23', 67.5, 77);
INSERT INTO products (id, category_id, name, price, stock) VALUES (24, 4, 'Product 24', 70.0, 76);
INSERT INTO products (id, category_id, name, price, stock) VALUES (25, 5, 'Product 25', 72.5, 75);
INSERT INTO products (id, category_id, name, price, stock) VALUES (26, 6, 'Product 26', 75.0, 74);
INSERT INTO products (id, category_id, name, price, stock) VALUES (27, 7, 'Product 27', 77.5, 73);
INSERT INTO products (id, category_id, name, price, stock) VALUES (28, 8, 'Product 28', 80.0, 72);
INSERT INTO products (id, category_id, name, price, stock) VALUES (29, 9, 'Product 29', 82.5, 71);
INSERT INTO products (id, category_id, name, price, stock) VALUES (30, 10, 'Product 30', 85.0, 70);
INSERT INTO products (id, category_id, name, price, stock) VALUES (31, 1, 'Product 31', 87.5, 69);
INSERT INTO products (id, category_id, name, price, stock) VALUES (32, 2, 'Product 32', 90.0, 68);
INSERT INTO products (id, category_id, name, price, stock) VALUES (33, 3, 'Product 33', 92.5, 67);
INSERT INTO products (id, category_id, name, price, stock) VALUES (34, 4, 'Product 34', 95.0, 66);
INSERT INTO products (id, category_id, name, price, stock) VALUES (35, 5, 'Product 35', 97.5, 65);
INSERT INTO products (id, category_id, name, price, stock) VALUES (36, 6, 'Product 36', 100.0, 64);
INSERT INTO products (id, category_id, name, price, stock) VALUES (37, 7, 'Product 37', 102.5, 63);
INSERT INTO products (id, category_id, name, price, stock) VALUES (38, 8, 'Product 38', 105.0, 62);
INSERT INTO products (id, category_id, name, price, stock) VALUES (39, 9, 'Product 39', 107.5, 61);
INSERT INTO products (id, category_id, name, price, stock) VALUES (40, 10, 'Product 40', 110.0, 60);
INSERT INTO users (id, username, email, created_at) VALUES (1, 'user1', 'user1@example.com', '2025-01-02 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (2, 'user2', 'user2@example.com', '2025-01-03 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (3, 'user3', 'user3@example.com', '2025-01-04 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (4, 'user4', 'user4@example.com', '2025-01-05 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (5, 'user5', 'user5@example.com', '2025-01-06 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (6, 'user6', 'user6@example.com', '2025-01-07 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (7, 'user7', 'user7@example.com', '2025-01-08 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (8, 'user8', 'user8@example.com', '2025-01-09 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (9, 'user9', 'user9@example.com', '2025-01-10 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (10, 'user10', 'user10@example.com', '2025-01-11 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (11, 'user11', 'user11@example.com', '2025-01-12 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (12, 'user12', 'user12@example.com', '2025-01-13 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (13, 'user13', 'user13@example.com', '2025-01-14 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (14, 'user14', 'user14@example.com', '2025-01-15 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (15, 'user15', 'user15@example.com', '2025-01-16 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (16, 'user16', 'user16@example.com', '2025-01-17 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (17, 'user17', 'user17@example.com', '2025-01-18 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (18, 'user18', 'user18@example.com', '2025-01-19 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (19, 'user19', 'user19@example.com', '2025-01-20 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (20, 'user20', 'user20@example.com', '2025-01-21 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (21, 'user21', 'user21@example.com', '2025-01-22 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (22, 'user22', 'user22@example.com', '2025-01-23 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (23, 'user23', 'user23@example.com', '2025-01-24 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (24, 'user24', 'user24@example.com', '2025-01-25 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (25, 'user25', 'user25@example.com', '2025-01-26 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (26, 'user26', 'user26@example.com', '2025-01-27 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (27, 'user27', 'user27@example.com', '2025-01-28 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (28, 'user28', 'user28@example.com', '2025-01-01 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (29, 'user29', 'user29@example.com', '2025-01-02 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (30, 'user30', 'user30@example.com', '2025-01-03 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (31, 'user31', 'user31@example.com', '2025-01-04 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (32, 'user32', 'user32@example.com', '2025-01-05 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (33, 'user33', 'user33@example.com', '2025-01-06 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (34, 'user34', 'user34@example.com', '2025-01-07 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (35, 'user35', 'user35@example.com', '2025-01-08 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (36, 'user36', 'user36@example.com', '2025-01-09 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (37, 'user37', 'user37@example.com', '2025-01-10 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (38, 'user38', 'user38@example.com', '2025-01-11 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (39, 'user39', 'user39@example.com', '2025-01-12 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (40, 'user40', 'user40@example.com', '2025-01-13 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (41, 'user41', 'user41@example.com', '2025-01-14 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (42, 'user42', 'user42@example.com', '2025-01-15 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (43, 'user43', 'user43@example.com', '2025-01-16 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (44, 'user44', 'user44@example.com', '2025-01-17 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (45, 'user45', 'user45@example.com', '2025-01-18 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (46, 'user46', 'user46@example.com', '2025-01-19 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (47, 'user47', 'user47@example.com', '2025-01-20 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (48, 'user48', 'user48@example.com', '2025-01-21 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (49, 'user49', 'user49@example.com', '2025-01-22 10:00:00');
INSERT INTO users (id, username, email, created_at) VALUES (50, 'user50', 'user50@example.com', '2025-01-23 10:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (1, 1, 'pending', 51.0, '2025-02-07 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (2, 2, 'shipped', 52.0, '2025-02-08 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (3, 3, 'delivered', 53.0, '2025-02-09 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (4, 4, 'cancelled', 54.0, '2025-02-10 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (5, 5, 'pending', 55.0, '2025-02-11 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (6, 6, 'shipped', 56.0, '2025-02-12 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (7, 7, 'delivered', 57.0, '2025-02-13 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (8, 8, 'cancelled', 58.0, '2025-02-14 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (9, 9, 'pending', 59.0, '2025-02-15 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (10, 10, 'shipped', 60.0, '2025-02-16 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (11, 11, 'delivered', 61.0, '2025-02-17 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (12, 12, 'cancelled', 62.0, '2025-02-18 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (13, 13, 'pending', 63.0, '2025-02-19 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (14, 14, 'shipped', 64.0, '2025-02-20 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (15, 15, 'delivered', 65.0, '2025-02-21 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (16, 16, 'cancelled', 66.0, '2025-02-22 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (17, 17, 'pending', 67.0, '2025-02-23 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (18, 18, 'shipped', 68.0, '2025-02-24 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (19, 19, 'delivered', 69.0, '2025-02-25 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (20, 20, 'cancelled', 70.0, '2025-02-26 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (21, 21, 'pending', 71.0, '2025-02-27 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (22, 22, 'shipped', 72.0, '2025-02-28 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (23, 23, 'delivered', 73.0, '2025-02-01 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (24, 24, 'cancelled', 74.0, '2025-02-02 11:00:00');
INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (25, 25, 'pending', 75.0, '2025-02-03 11:00:00');
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (1, 1, 1, 1, 12.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (2, 2, 2, 2, 15.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (3, 3, 3, 3, 17.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (4, 4, 4, 4, 20.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (5, 5, 5, 5, 22.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (6, 6, 6, 1, 25.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (7, 7, 7, 2, 27.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (8, 8, 8, 3, 30.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (9, 9, 9, 4, 32.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (10, 10, 10, 5, 35.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (11, 11, 11, 1, 37.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (12, 12, 12, 2, 40.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (13, 13, 13, 3, 42.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (14, 14, 14, 4, 45.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (15, 15, 15, 5, 47.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (16, 16, 16, 1, 50.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (17, 17, 17, 2, 52.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (18, 18, 18, 3, 55.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (19, 19, 19, 4, 57.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (20, 20, 20, 5, 60.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (21, 21, 21, 1, 62.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (22, 22, 22, 2, 65.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (23, 23, 23, 3, 67.5);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (24, 24, 24, 4, 70.0);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (25, 25, 25, 5, 72.5);
