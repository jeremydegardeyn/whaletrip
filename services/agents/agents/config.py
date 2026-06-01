"""
Shared agent configuration — reads model names from environment variables.

To change models without a code deploy, update the Cloud Run env vars:
  COORDINATOR_MODEL  — the root coordinator agent (default: gemini-3-flash)
  AGENT_MODEL        — all specialist sub-agents (default: gemini-3-flash)

Example override via gcloud:
  gcloud run services update whaletrip-agents --region=us-central1 \\
    --update-env-vars COORDINATOR_MODEL=gemini-3.5-flash,AGENT_MODEL=gemini-3-flash
"""
import os

COORDINATOR_MODEL: str = os.environ.get("COORDINATOR_MODEL", "gemini-3-flash")
AGENT_MODEL: str = os.environ.get("AGENT_MODEL", "gemini-3-flash")
