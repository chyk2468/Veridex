"""
Evaluation execution script.
Run with: python scripts/evaluate.py
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from evaluation.benchmark import BenchmarkRunner

if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.print_report()
