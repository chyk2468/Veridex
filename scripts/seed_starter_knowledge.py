"""
CLI script to seed the starter knowledge base.
Usage:
    python scripts/seed_starter_knowledge.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from storage.seeder import seed_starter_knowledge

if __name__ == "__main__":
    print("Seeding Starter Knowledge Base with assignment PDF disclosures...")
    res = seed_starter_knowledge(reset=True)
    print("Result:", res)
    print("\nKnowledge base successfully seeded and synchronized!")
