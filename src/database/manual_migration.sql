-- Manual database migration (pre-Alembic)
-- DEPRECATED: Will be replaced by Alembic in WP2.4

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crushes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS relation_chains (
    id SERIAL PRIMARY KEY,
    crush_id INTEGER REFERENCES crushes(id),
    chain_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS context_embeddings (
    id SERIAL PRIMARY KEY,
    crush_id INTEGER REFERENCES crushes(id),
    embedding vector(1536),
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
