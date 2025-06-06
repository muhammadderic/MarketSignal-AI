# === Orchestration: News Scoring ===
# Bounds on the number of (id, title) pairs the news scoring orchestrator
# will accept before proceeding with downstream LLM scoring.
#
# - Below MIN: not enough signal to justify an LLM batch call.
# - Above MAX: protect against runaway LLM cost / context explosion.
NEWS_SCORING_MIN_TITLE_PAIRS: int = 5
NEWS_SCORING_MAX_TITLE_PAIRS: int = 10