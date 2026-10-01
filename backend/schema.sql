CREATE TABLE IF NOT EXISTS customers (
 customer_id SERIAL PRIMARY KEY,
 customer_name VARCHAR(120) NOT NULL,
 customer_email VARCHAR(255) NOT NULL UNIQUE,
 phone_number VARCHAR(40),
 newsletter_signup BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS reservations (
 reservation_id SERIAL PRIMARY KEY,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
 time_slot TIMESTAMPTZ NOT NULL,
 table_number INTEGER NOT NULL CHECK(table_number BETWEEN 1 AND 30),
 number_of_guests INTEGER NOT NULL CHECK(number_of_guests BETWEEN 1 AND 20),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(time_slot, table_number)
);
CREATE INDEX IF NOT EXISTS idx_reservations_time_slot ON reservations(time_slot);
CREATE TABLE IF NOT EXISTS newsletter_signups (
 signup_id SERIAL PRIMARY KEY,
 email VARCHAR(255) NOT NULL UNIQUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
