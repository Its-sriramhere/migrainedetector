import psycopg

conn = psycopg.connect(host='db.lrulmcudqdlidhldncok.supabase.co', port=5432, dbname='postgres', user='postgres', password='Headachepps@247', sslmode='require')
conn.autocommit = True
cur = conn.cursor()

tables = ["users", "assessment_questions", "user_profiles", "assessment_responses",
          "user_risk_profiles", "devices", "sensor_readings", "migraine_episodes",
          "predictions", "prediction_features", "alerts", "alert_advice",
          "notification_logs", "datasets"]

for t in tables:
    cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    print(f"truncated: {t}")

cur.close()
conn.close()
print("done")