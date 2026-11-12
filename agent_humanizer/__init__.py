"""agent-humanizer: make AI-written text read like a careful person wrote it.

Two passes, stdlib only, no network, no keys:
  1. strip the tells — stock AI phrases, hedges and filler openers (EN + FA)
  2. rebuild toward controlled English — one idea per sentence, safe
     passives rewritten to active voice (STE80, 80% of the way)
"""

__version__ = "0.1.0"
