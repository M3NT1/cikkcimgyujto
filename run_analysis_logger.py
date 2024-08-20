import sqlite3
import json
from datetime import datetime


class RunAnalysisLogger:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Futási információk táblája
        c.execute('''CREATE TABLE IF NOT EXISTS run_info
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      run_time TEXT,
                      document_count INTEGER,
                      unique_tokens INTEGER,
                      corpus_positions INTEGER,
                      gensim_version TEXT,
                      python_version TEXT,
                      platform TEXT,
                      lda_topics INTEGER,
                      lda_passes INTEGER,
                      lda_iterations INTEGER,
                      lda_training_time REAL)''')

        # Téma elemzés táblája
        c.execute('''CREATE TABLE IF NOT EXISTS topic_analysis
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      run_id INTEGER,
                      topic_id INTEGER,
                      top_words TEXT,
                      avg_sentiment REAL,
                      frequency INTEGER,
                      FOREIGN KEY (run_id) REFERENCES run_info(id))''')

        conn.commit()
        conn.close()

    def log_run(self, document_count, unique_tokens, corpus_positions,
                gensim_version, python_version, platform,
                lda_topics, lda_passes, lda_iterations, lda_training_time,
                topic_analysis):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Futási információk beszúrása
        c.execute('''INSERT INTO run_info
                     (run_time, document_count, unique_tokens, corpus_positions,
                      gensim_version, python_version, platform,
                      lda_topics, lda_passes, lda_iterations, lda_training_time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), document_count, unique_tokens, corpus_positions,
                   gensim_version, python_version, platform,
                   lda_topics, lda_passes, lda_iterations, lda_training_time))

        run_id = c.lastrowid

        # Téma elemzés beszúrása
        for topic in topic_analysis:
            c.execute('''INSERT INTO topic_analysis
                         (run_id, topic_id, top_words, avg_sentiment, frequency)
                         VALUES (?, ?, ?, ?, ?)''',
                      (run_id, topic['topic_id'], json.dumps(topic['top_words']),
                       topic['avg_sentiment'], topic['frequency']))

        conn.commit()
        conn.close()

    def get_latest_run(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM run_info ORDER BY id DESC LIMIT 1')
        run_info = c.fetchone()

        if run_info:
            run_id = run_info[0]
            c.execute('SELECT * FROM topic_analysis WHERE run_id = ?', (run_id,))
            topics = c.fetchall()

            conn.close()

            return {
                'run_info': {
                    'id': run_info[0],
                    'run_time': run_info[1],
                    'document_count': run_info[2],
                    'unique_tokens': run_info[3],
                    'corpus_positions': run_info[4],
                    'gensim_version': run_info[5],
                    'python_version': run_info[6],
                    'platform': run_info[7],
                    'lda_topics': run_info[8],
                    'lda_passes': run_info[9],
                    'lda_iterations': run_info[10],
                    'lda_training_time': run_info[11]
                },
                'topic_analysis': [
                    {
                        'topic_id': topic[2],
                        'top_words': json.loads(topic[3]),
                        'avg_sentiment': topic[4],
                        'frequency': topic[5]
                    } for topic in topics
                ]
            }

        conn.close()
        return None

    def get_all_runs(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM run_info ORDER BY run_time DESC')
        all_runs = c.fetchall()

        results = []
        for run in all_runs:
            run_id = run[0]
            c.execute('SELECT * FROM topic_analysis WHERE run_id = ?', (run_id,))
            topics = c.fetchall()

            results.append({
                'run_info': {
                    'id': run[0],
                    'run_time': run[1],
                    'document_count': run[2],
                    'unique_tokens': run[3],
                    'corpus_positions': run[4],
                    'gensim_version': run[5],
                    'python_version': run[6],
                    'platform': run[7],
                    'lda_topics': run[8],
                    'lda_passes': run[9],
                    'lda_iterations': run[10],
                    'lda_training_time': run[11]
                },
                'topic_analysis': [
                    {
                        'topic_id': topic[2],
                        'top_words': json.loads(topic[3]),
                        'avg_sentiment': topic[4],
                        'frequency': topic[5]
                    } for topic in topics
                ]
            })

        conn.close()
        return results
