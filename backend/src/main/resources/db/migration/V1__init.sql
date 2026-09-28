CREATE TABLE customers (
    id               UUID PRIMARY KEY,
    customer_number  VARCHAR(32)  NOT NULL UNIQUE,
    full_name        VARCHAR(120) NOT NULL,
    real_pin_hash    VARCHAR(100) NOT NULL,
    role             VARCHAR(32)  NOT NULL,
    failed_attempts  INT          NOT NULL DEFAULT 0,
    locked_until     TIMESTAMPTZ
);

CREATE TABLE duress_credentials (
    id           UUID PRIMARY KEY,
    customer_id  UUID         NOT NULL REFERENCES customers(id),
    pin_hash     VARCHAR(100) NOT NULL,
    active       BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_duress_credentials_customer ON duress_credentials(customer_id);

CREATE TABLE accounts (
    id              UUID PRIMARY KEY,
    customer_id     UUID          NOT NULL UNIQUE REFERENCES customers(id),
    account_number  VARCHAR(32)   NOT NULL UNIQUE,
    real_balance    NUMERIC(19,2) NOT NULL CHECK (real_balance >= 0),
    duress_balance  NUMERIC(19,2) NOT NULL CHECK (duress_balance >= 0)
);

CREATE TABLE transactions (
    id             UUID PRIMARY KEY,
    account_id     UUID          NOT NULL REFERENCES accounts(id),
    type           VARCHAR(32)   NOT NULL,
    amount         NUMERIC(19,2) NOT NULL CHECK (amount > 0),
    mode           VARCHAR(16)   NOT NULL,
    balance_after  NUMERIC(19,2) NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL
);
CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at DESC);

CREATE TABLE auth_sessions (
    id           UUID PRIMARY KEY,
    customer_id  UUID        NOT NULL REFERENCES customers(id),
    mode         VARCHAR(16) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE security_events (
    id           UUID PRIMARY KEY,
    customer_id  UUID,
    session_id   UUID,
    event_type   VARCHAR(48) NOT NULL,
    severity     VARCHAR(16) NOT NULL,
    details      TEXT,
    created_at   TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_security_events_created ON security_events(created_at DESC);
