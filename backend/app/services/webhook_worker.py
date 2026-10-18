"""
MiroFish Enterprise Webhook Queue & DLQ Re-drive Worker (Agent 20: DevOps & Failover Guard)
Periodically sweeps Dead-Letter Queue (DLQ) and re-drives pending webhooks.
"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.services.webhook_service import webhook_dispatcher

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [WEBHOOK-WORKER] %(message)s")

POLL_INTERVAL_SECONDS = int(os.environ.get("WEBHOOK_WORKER_POLL_INTERVAL", 15))


def run_worker():
    logging.info(f"Webhook Background Worker started. Poll interval: {POLL_INTERVAL_SECONDS}s")
    try:
        while True:
            try:
                dlq_items = webhook_dispatcher.get_dlq(limit=10)
                if dlq_items:
                    logging.info(f"Found {len(dlq_items)} items in DLQ. Executing automated re-drive...")
                    results = webhook_dispatcher.replay_all_dlq()
                    success_count = sum(1 for r in results if r.is_success)
                    logging.info(f"Re-drive completed: {success_count}/{len(results)} successful.")
                time.sleep(POLL_INTERVAL_SECONDS)
            except Exception as e:
                logging.error(f"Worker iteration error: {str(e)}")
                time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Webhook worker exiting cleanly.")


if __name__ == "__main__":
    run_worker()
