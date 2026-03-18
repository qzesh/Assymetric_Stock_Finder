import sqlite3
import json

conn = sqlite3.connect('discovery_checkpoint.db')
cursor = conn.cursor()

cursor.execute('SELECT validation_result FROM analysis_results WHERE ticker = ?', ('ACIW',))
result = cursor.fetchone()
if result:
    val = json.loads(result[0])
    stages = val.get('stages', {})
    pattern = stages.get('pattern_detection', {})
    print('ACIW Pattern Detection:')
    print(json.dumps(pattern, indent=2))
    print('\nConviction:', val.get('conviction'))
conn.close()
