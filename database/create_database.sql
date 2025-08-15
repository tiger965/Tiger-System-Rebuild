-- Tiger System Database Schema
-- Version: 1.0
-- Author: Window-1

-- Create database
CREATE DATABASE IF NOT EXISTS tiger_system;

-- Use the database
\c tiger_system;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================
-- 1. Market Data Table
-- =============================================
CREATE TABLE IF NOT EXISTS market_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    open_24h DECIMAL(20, 8),
    bid_price DECIMAL(20, 8),
    ask_price DECIMAL(20, 8),
    bid_volume DECIMAL(20, 8),
    ask_volume DECIMAL(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT market_data_unique UNIQUE(timestamp, symbol, exchange)
) PARTITION BY RANGE (timestamp);

-- Create indexes for market_data
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_exchange ON market_data(exchange);
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);

-- =============================================
-- 2. Chain Data Table
-- =============================================
CREATE TABLE IF NOT EXISTS chain_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    chain VARCHAR(50) NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(100) UNIQUE NOT NULL,
    from_address VARCHAR(100) NOT NULL,
    to_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20),
    amount DECIMAL(30, 18),
    gas_used BIGINT,
    gas_price DECIMAL(20, 8),
    transaction_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create indexes for chain_data
CREATE INDEX idx_chain_data_timestamp ON chain_data(timestamp DESC);
CREATE INDEX idx_chain_data_chain ON chain_data(chain);
CREATE INDEX idx_chain_data_from_address ON chain_data(from_address);
CREATE INDEX idx_chain_data_to_address ON chain_data(to_address);
CREATE INDEX idx_chain_data_token_symbol ON chain_data(token_symbol);
CREATE INDEX idx_chain_data_metadata ON chain_data USING GIN(metadata);

-- =============================================
-- 3. Social Sentiment Table
-- =============================================
CREATE TABLE IF NOT EXISTS social_sentiment (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(50) NOT NULL, -- twitter, reddit, telegram, etc
    symbol VARCHAR(20),
    content TEXT,
    author VARCHAR(100),
    sentiment_score DECIMAL(5, 4), -- -1 to 1
    engagement_score INTEGER,
    reach INTEGER,
    url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create indexes for social_sentiment
CREATE INDEX idx_social_sentiment_timestamp ON social_sentiment(timestamp DESC);
CREATE INDEX idx_social_sentiment_source ON social_sentiment(source);
CREATE INDEX idx_social_sentiment_symbol ON social_sentiment(symbol);
CREATE INDEX idx_social_sentiment_sentiment_score ON social_sentiment(sentiment_score);

-- =============================================
-- 4. News Events Table
-- =============================================
CREATE TABLE IF NOT EXISTS news_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    url VARCHAR(500) UNIQUE,
    category VARCHAR(50),
    importance VARCHAR(20), -- low, medium, high, critical
    symbols TEXT[], -- array of related symbols
    sentiment_score DECIMAL(5, 4),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create indexes for news_events
CREATE INDEX idx_news_events_timestamp ON news_events(timestamp DESC);
CREATE INDEX idx_news_events_source ON news_events(source);
CREATE INDEX idx_news_events_importance ON news_events(importance);
CREATE INDEX idx_news_events_symbols ON news_events USING GIN(symbols);

-- =============================================
-- 5. Trader Actions Table
-- =============================================
CREATE TABLE IF NOT EXISTS trader_actions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    trader_address VARCHAR(100) NOT NULL,
    trader_label VARCHAR(100), -- whale, smart_money, etc
    action_type VARCHAR(50) NOT NULL, -- buy, sell, stake, unstake, etc
    symbol VARCHAR(20) NOT NULL,
    amount DECIMAL(30, 18),
    price DECIMAL(20, 8),
    chain VARCHAR(50),
    transaction_hash VARCHAR(100),
    profit_loss DECIMAL(20, 8),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create indexes for trader_actions
CREATE INDEX idx_trader_actions_timestamp ON trader_actions(timestamp DESC);
CREATE INDEX idx_trader_actions_trader_address ON trader_actions(trader_address);
CREATE INDEX idx_trader_actions_symbol ON trader_actions(symbol);
CREATE INDEX idx_trader_actions_action_type ON trader_actions(action_type);

-- =============================================
-- 6. Signals Table
-- =============================================
CREATE TABLE IF NOT EXISTS signals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    signal_type VARCHAR(50) NOT NULL, -- buy, sell, alert
    symbol VARCHAR(20) NOT NULL,
    source VARCHAR(100) NOT NULL, -- technical, sentiment, whale_alert, etc
    confidence DECIMAL(5, 4) NOT NULL, -- 0 to 1
    trigger_reason TEXT NOT NULL,
    target_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    time_horizon VARCHAR(20), -- short, medium, long
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'active', -- active, expired, executed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for signals
CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_signal_type ON signals(signal_type);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_confidence ON signals(confidence DESC);

-- =============================================
-- 7. Trades Table
-- =============================================
CREATE TABLE IF NOT EXISTS trades (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    signal_id UUID REFERENCES signals(id),
    symbol VARCHAR(20) NOT NULL,
    trade_type VARCHAR(20) NOT NULL, -- buy, sell
    suggested_price DECIMAL(20, 8),
    suggested_amount DECIMAL(20, 8),
    actual_price DECIMAL(20, 8),
    actual_amount DECIMAL(20, 8),
    exchange VARCHAR(50),
    status VARCHAR(20) NOT NULL, -- pending, executed, cancelled, failed
    profit_loss DECIMAL(20, 8),
    fees DECIMAL(20, 8),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for trades
CREATE INDEX idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX idx_trades_signal_id ON trades(signal_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);

-- =============================================
-- 8. System Logs Table
-- =============================================
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_id INTEGER NOT NULL, -- 1-10
    log_level VARCHAR(20) NOT NULL, -- debug, info, warning, error, critical
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    error_trace TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create indexes for system_logs
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_window_id ON system_logs(window_id);
CREATE INDEX idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_component ON system_logs(component);

-- =============================================
-- 9. Learning Data Table
-- =============================================
CREATE TABLE IF NOT EXISTS learning_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    training_data JSONB NOT NULL,
    performance_metrics JSONB,
    parameters JSONB,
    status VARCHAR(20) NOT NULL, -- training, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for learning_data
CREATE INDEX idx_learning_data_timestamp ON learning_data(timestamp DESC);
CREATE INDEX idx_learning_data_model_name ON learning_data(model_name);
CREATE INDEX idx_learning_data_status ON learning_data(status);

-- =============================================
-- Create Partitions for Time-Series Tables
-- =============================================

-- Function to create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partitions(table_name text, start_date date, end_date date)
RETURNS void AS $$
DECLARE
    partition_date date := start_date;
    partition_name text;
BEGIN
    WHILE partition_date < end_date LOOP
        partition_name := table_name || '_' || to_char(partition_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I 
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, 
                       table_name,
                       partition_date,
                       partition_date + interval '1 month');
        
        partition_date := partition_date + interval '1 month';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create partitions for the next 12 months
SELECT create_monthly_partitions('market_data', '2024-01-01'::date, '2025-01-01'::date);
SELECT create_monthly_partitions('chain_data', '2024-01-01'::date, '2025-01-01'::date);
SELECT create_monthly_partitions('social_sentiment', '2024-01-01'::date, '2025-01-01'::date);
SELECT create_monthly_partitions('news_events', '2024-01-01'::date, '2025-01-01'::date);
SELECT create_monthly_partitions('trader_actions', '2024-01-01'::date, '2025-01-01'::date);
SELECT create_monthly_partitions('system_logs', '2024-01-01'::date, '2025-01-01'::date);

-- =============================================
-- Create Archive Tables
-- =============================================

-- Function to archive old data
CREATE OR REPLACE FUNCTION archive_old_data()
RETURNS void AS $$
BEGIN
    -- Archive data older than 30 days
    -- This is a placeholder - actual implementation would move data to archive tables
    RAISE NOTICE 'Archiving old data...';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Create Triggers for Updated Timestamps
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_data_updated_at BEFORE UPDATE ON learning_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- Create Views for Common Queries
-- =============================================

-- Recent market data view
CREATE OR REPLACE VIEW recent_market_data AS
SELECT * FROM market_data 
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Active signals view
CREATE OR REPLACE VIEW active_signals AS
SELECT * FROM signals 
WHERE status = 'active' 
  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY confidence DESC, timestamp DESC;

-- System health view
CREATE OR REPLACE VIEW system_health AS
SELECT 
    window_id,
    COUNT(*) as log_count,
    COUNT(CASE WHEN log_level = 'error' THEN 1 END) as error_count,
    COUNT(CASE WHEN log_level = 'warning' THEN 1 END) as warning_count,
    MAX(timestamp) as last_activity
FROM system_logs
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY window_id;

-- =============================================
-- Grant Permissions
-- =============================================

-- Create application user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'tiger_app') THEN
        CREATE USER tiger_app WITH PASSWORD 'tiger_secure_password_2024';
    END IF;
END $$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE tiger_system TO tiger_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiger_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiger_app;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO tiger_app;

-- =============================================
-- Database Configuration
-- =============================================

-- Set optimal configuration for time-series data
ALTER DATABASE tiger_system SET shared_buffers = '256MB';
ALTER DATABASE tiger_system SET effective_cache_size = '1GB';
ALTER DATABASE tiger_system SET maintenance_work_mem = '128MB';
ALTER DATABASE tiger_system SET checkpoint_completion_target = 0.9;
ALTER DATABASE tiger_system SET wal_buffers = '16MB';
ALTER DATABASE tiger_system SET default_statistics_target = 100;
ALTER DATABASE tiger_system SET random_page_cost = 1.1;

COMMENT ON DATABASE tiger_system IS 'Tiger Intelligent Trading Analysis System Database';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
    RAISE NOTICE 'Tables: 9';
    RAISE NOTICE 'Indexes: Created';
    RAISE NOTICE 'Partitions: Created for next 12 months';
    RAISE NOTICE 'User: tiger_app created with permissions';
END $$;