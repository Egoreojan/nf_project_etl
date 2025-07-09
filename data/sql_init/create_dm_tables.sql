CREATE SCHEMA IF NOT EXISTS DM;

-- Таблица Обороты
CREATE TABLE DM.DM_ACCOUNT_TURNOVER_F (
    on_date DATE,
    account_rk INTEGER,
    credit_ammount DECIMAL(23,8),
    credit_amount_rub DECIMAL(23,8),
    debet_amount DECIMAL(23,8),
    debet_amount_rub DECIMAL(23,8)
);

-- Таблица Остатки
CREATE TABLE DM.DM_ACCOUNT_BALANCE_F (
    on_date DATE,
    account_rk INTEGER,
    balance_out DECIMAL(23,8),
    balance_out_rub DECIMAL(23,8)
);

-- Таблица 101 форма
CREATE TABLE DM.DM_F101_ROUND_F (
    from_date DATE,
    to_date DATE,
    chapter VARCHAR(1),
    ledger_account VARCHAR(5),
    characteristic VARCHAR(1),
    balance_in_rub DECIMAL(23,8),
    balance_in_val DECIMAL(23,8),
    balance_in_total DECIMAL(23,8),
    turn_deb_rub DECIMAL(23,8),
    turn_deb_val DECIMAL(23,8),
    turn_deb_total DECIMAL(23,8),
    turn_cre_rub DECIMAL(23,8),
    turn_cre_val DECIMAL(23,8),
    turn_cre_total DECIMAL(23,8),
    balance_out_rub DECIMAL(23,8),
    balance_out_val DECIMAL(23,8),
    balance_out_total DECIMAL(23,8)
);