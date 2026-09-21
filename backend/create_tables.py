import psycopg

conn = psycopg.connect(host='db.lrulmcudqdlidhldncok.supabase.co', port=5432, dbname='postgres', user='postgres', password='Headachepps@247', sslmode='require')
conn.autocommit = True
cur = conn.cursor()

# Create all tables
tables = [
    ('users', '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(120) DEFAULT '',
            email VARCHAR(255) UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            consent_given BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('user_profiles', '''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id),
            date_of_birth VARCHAR(20),
            migraine_history VARCHAR(60),
            typical_frequency VARCHAR(60),
            typical_duration VARCHAR(60),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('assessment_questions', '''
        CREATE TABLE IF NOT EXISTS assessment_questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            question_type VARCHAR(20) DEFAULT 'single',
            options JSON DEFAULT '[]',
            active BOOLEAN DEFAULT TRUE
        )
    '''),
    ('assessment_responses', '''
        CREATE TABLE IF NOT EXISTS assessment_responses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            question_id INTEGER REFERENCES assessment_questions(id),
            answer TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('user_risk_profiles', '''
        CREATE TABLE IF NOT EXISTS user_risk_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id),
            migraine_history_score FLOAT DEFAULT 0.0,
            sleep_profile VARCHAR(60),
            stress_profile VARCHAR(60),
            activity_profile VARCHAR(60),
            hydration_profile VARCHAR(60),
            caffeine_profile VARCHAR(60),
            trigger_profile JSON DEFAULT '[]',
            sleep_hours FLOAT,
            resting_hr FLOAT,
            profile_version VARCHAR(20) DEFAULT 'v1',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('devices', '''
        CREATE TABLE IF NOT EXISTS devices (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            device_identifier VARCHAR(120) UNIQUE,
            device_name VARCHAR(120) DEFAULT 'Raspberry Pi',
            status VARCHAR(20) DEFAULT 'online',
            last_seen TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('sensor_readings', '''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            device_id INTEGER REFERENCES devices(id),
            source VARCHAR(20) DEFAULT 'pi',
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            heart_rate FLOAT,
            hrv FLOAT,
            systolic_bp FLOAT,
            diastolic_bp FLOAT,
            spo2 FLOAT,
            temperature FLOAT,
            activity FLOAT,
            signal_quality FLOAT DEFAULT 1.0
        )
    '''),
    ('migraine_episodes', '''
        CREATE TABLE IF NOT EXISTS migraine_episodes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            end_time TIMESTAMP WITHOUT TIME ZONE,
            severity VARCHAR(20),
            symptoms JSON DEFAULT '[]',
            trigger VARCHAR(120),
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('predictions', '''
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            risk_score FLOAT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            prediction_window INTEGER DEFAULT 60,
            model_version VARCHAR(20) DEFAULT 'heuristic-v1',
            outcome VARCHAR(20) DEFAULT 'pending',
            source VARCHAR(20) DEFAULT 'pi',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('prediction_features', '''
        CREATE TABLE IF NOT EXISTS prediction_features (
            id SERIAL PRIMARY KEY,
            prediction_id INTEGER REFERENCES predictions(id),
            feature_name VARCHAR(120) NOT NULL,
            feature_value FLOAT,
            contribution FLOAT NOT NULL
        )
    '''),
    ('alerts', '''
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            prediction_id INTEGER REFERENCES predictions(id),
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            risk_score FLOAT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            acknowledged BOOLEAN DEFAULT FALSE,
            feedback VARCHAR(20),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('notification_logs', '''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            alert_id INTEGER REFERENCES alerts(id),
            kind VARCHAR(20) DEFAULT 'sms',
            provider VARCHAR(20) DEFAULT 'mock',
            recipient VARCHAR(120),
            risk_level VARCHAR(20),
            status VARCHAR(20) DEFAULT 'sent',
            detail VARCHAR(255),
            message TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
    '''),
    ('alert_advice', '''
        CREATE TABLE IF NOT EXISTS alert_advice (
            id SERIAL PRIMARY KEY,
            alert_id INTEGER REFERENCES alerts(id),
            step INTEGER DEFAULT 1,
            guidance TEXT NOT NULL
        )
    '''),
    ('datasets', '''
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE,
            path VARCHAR(1024),
            rows INTEGER DEFAULT 0,
            columns JSON DEFAULT '[]',
            size_bytes INTEGER DEFAULT 0,
            modified FLOAT,
            storage_bucket VARCHAR(120) DEFAULT 'datasets',
            storage_key VARCHAR(255) DEFAULT '',
            stored BOOLEAN DEFAULT FALSE,
            uploaded_at TIMESTAMP WITHOUT TIME ZONE
        )
    '''),
]

for table_name, ddl in tables:
    try:
        cur.execute(ddl)
        print(f"Created: {table_name}")
    except Exception as e:
        print(f"Error {table_name}: {e}")

cur.close()
conn.close()
print("Done!")