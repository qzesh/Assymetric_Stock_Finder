"""
Test AI reasoning on top candidate (INTA)
"""

import sqlite3
import json
from ai_reasoner import AIReasoningEngine

# Load INTA validation from checkpoint
conn = sqlite3.connect('discovery_checkpoint.db')
cursor = conn.cursor()
cursor.execute('SELECT validation_result FROM analysis_results WHERE ticker = ?', ('INTA',))
result = cursor.fetchone()
conn.close()

if not result:
    print("❌ INTA validation not found in checkpoint database")
    exit(1)

validation_data = json.loads(result[0])

print("📊 Analyzing INTA with AI Reasoning Engine\n")
print("="*80)

try:
    engine = AIReasoningEngine()
    
    analysis = engine.analyze_candidate('INTA', validation_data)
    
    if analysis.get('status') == 'success':
        print("✅ AI Analysis Complete\n")
        print(analysis['ai_analysis'])
    else:
        print(f"❌ Analysis failed: {analysis.get('error')}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "="*80)
print("Note: AI reasoning requires Claude API calls (paid)")
