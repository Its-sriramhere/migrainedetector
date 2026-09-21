import psycopg

conn = psycopg.connect('dbname=postgres user=postgres password=Headachepps@247 host=db.lrulmcudqdlidhldncok.supabase.co port=5432 sslmode=require')
conn.autocommit = True
cur = conn.cursor()

# Create extension
cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
print('Extension done')

# Define all table DDLs based on app/models
tables_ddl = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'user_profiles': '''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            full_name VARCHAR(255),
            email_verified BOOLEAN DEFAULT FALSE,
            picture VARCHAR(500),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'assessment_questions': '''
        CREATE TABLE IF NOT EXISTS assessment_questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            question_type VARCHAR(50) NOT NULL,
            options JSONB,
            score_weight INTEGER DEFAULT 1,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'assessment_responses': '''
        CREATE TABLE IF NOT EXISTS assessment_responses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES assessment_questions(id) ON DELETE CASCADE,
            response_value VARCHAR(255),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'user_risk_profiles': '''
        CREATE TABLE IF NOT EXISTS user_risk_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            risk_level VARCHAR(20) DEFAULT 'low',
            risk_score INTEGER DEFAULT 0,
            last_assessment TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'devices': '''
        CREATE TABLE IF NOT EXISTS devices (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            device_identifier VARCHAR(120) NOT NULL,
            device_name VARCHAR(120),
            status VARCHAR(20),
            last_seen TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'sensor_readings': '''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            heart_rate INTEGER,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            spo2 INTEGER,
            temperature FLOAT,
            activity FLOAT,
            timestamp TIMESTAMP WITHOUT TIME ZONE,
            source VARCHAR(50),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'migraine_episodes': '''
        CREATE TABLE IF NOT EXISTS migraine_episodes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            start_time TIMESTAMP WITHOUT TIME ZONE,
            end_time TIMESTAMP WITHOUT TIME ZONE,
            severity VARCHAR(20),
            symptoms JSONB,
            triggers JSONB,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'predictions': '''
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            risk_score INTEGER DEFAULT 0,
            risk_level VARCHAR(20) DEFAULT 'low',
            features JSONB,
            advice TEXT[],
            prediction_window_minutes INTEGER DEFAULT 60,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'prediction_features': '''
        CREATE TABLE IF NOT EXISTS prediction_features (
            id SERIAL PRIMARY KEY,
            prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
            feature_name VARCHAR(50) NOT NULL,
            feature_value FLOAT NOT NULL,
            contribution FLOAT DEFAULT 0.0
        )
    ''',
    'alerts': '''
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            advice TEXT[] DEFAULT '{}'
        )
    ''',
    'notification_logs': '''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            sent_at TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'alert_advice': '''
        CREATE TABLE IF NOT EXISTS alert_advice (
            id SERIAL PRIMARY KEY,
            alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
            step INTEGER NOT NULL,
            guidance TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    ''',
    'datasets': '''
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            storage_key VARCHAR(500),
            supabase_stored BOOLEAN DEFAULT FALSE,
            file_size INTEGER,
            uploaded_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        )
    '''
}

for table_name, ddl in tables_ddl.items():
    try:
        cur.execute(ddl)
        print(f'Created/verified table: {table_name}')
    except Exception as e:
        print(f'Error creating {table_name}: {e}')

cur.close()
conn.close()
print('All tables initialized!')