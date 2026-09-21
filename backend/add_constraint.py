import sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')
import psycopg

conn = psycopg.connect(host='db.lrulmcudqdlidhldncok.supabase.co', port=5432, dbname='postgres', user='postgres', password='Headachepps@247', sslmode='require')
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_question') THEN
    DELETE FROM assessment_responses WHERE id IN (
      SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id, question_id ORDER BY id) as rn
        FROM assessment_responses
      ) t WHERE rn > 1
    );
    ALTER TABLE assessment_responses ADD CONSTRAINT uq_user_question UNIQUE (user_id, question_id);
  END IF;
END $$;
""")
print('Constraint added')
cur.close()
conn.close()