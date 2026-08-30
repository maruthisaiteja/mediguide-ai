"""
MediGuide Vision AI — Top-Level Application Entrypoint
======================================================
Exposes the FastAPI `app` instance for Vercel Serverless and Uvicorn.
For local Streamlit UI, run: `streamlit run streamlit_app.py`
"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.index import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
