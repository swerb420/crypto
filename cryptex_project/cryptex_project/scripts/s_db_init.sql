-- Drop tables to ensure a clean slate
DROP TABLE IF EXISTS public.trading_signals;
DROP TABLE IF EXISTS public.monitored_traders;

-- Re-create tables with the final, complete schema
CREATE TABLE IF NOT EXISTS public.monitored_traders (id SERIAL PRIMARY KEY, identifier VARCHAR(255) NOT NULL UNIQUE, exchange VARCHAR(100) NOT NULL, description TEXT, is_active BOOLEAN DEFAULT TRUE);
CREATE TABLE IF NOT EXISTS public.recent_trades (id SERIAL PRIMARY KEY, ingested_at TIMESTAMPTZ DEFAULT NOW(), trader_id VARCHAR(255), asset VARCHAR(50), raw_data JSONB);
CREATE TABLE IF NOT EXISTS public.recent_catalysts (id SERIAL PRIMARY KEY, ingested_at TIMESTAMPTZ DEFAULT NOW(), headline TEXT, source VARCHAR(100), asset_tags TEXT[], raw_data JSONB);

CREATE TABLE IF NOT EXISTS public.trading_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    trader_id VARCHAR(255),
    exchange VARCHAR(100),
    asset VARCHAR(50),
    direction VARCHAR(10),
    entry_price NUMERIC, -- Added for PnL tracking
    trade_size_usd NUMERIC,
    catalyst_headline TEXT,
    safety_rating VARCHAR(50),
    ai_confidence_score INT,
    ai_summary TEXT,
    trade_status VARCHAR(50) DEFAULT 'SIGNAL' -- e.g., SIGNAL, OPEN, CLOSED
);

-- Insert a starting wallet
INSERT INTO public.monitored_traders (identifier, exchange, description, is_active) VALUES ('0x1AD8b62573212c5B41A6a061A22A933A44a86835', 'ethereum', 'Example ETH Whale', TRUE) ON CONFLICT (identifier) DO NOTHING;