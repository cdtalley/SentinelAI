"""
Pluggable production concerns (auth, logging, rate limits).

Swap implementations via settings — routes depend on stable FastAPI Depends()
targets in ``app.modules.*`` rather than importing concrete vendors directly.
"""
