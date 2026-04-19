import logging
from time import sleep

from app.core.settings import get_settings
from app.db.warehouse import Warehouse
from app.pipeline.sync import run_sync, utc_now_iso, write_sync_status


logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    warehouse = Warehouse(settings)
    warehouse.initialize()
    interval_seconds = max(settings.sync_interval_hours, 1) * 3600
    while True:
        try:
            run_sync()
        except Exception as exc:
            logger.exception("Scheduled sync failed.")

            current_status = warehouse.query_df("select * from sync_status limit 1")
            should_write_fallback = current_status.empty

            if not current_status.empty:
                record = current_status.iloc[0].to_dict()
                should_write_fallback = str(record.get("status") or "").lower() != "failed"

            if should_write_fallback:
                started_at = None
                if not current_status.empty:
                    started_at = current_status.iloc[0].get("started_at")
                    if started_at is not None and hasattr(started_at, "isoformat"):
                        started_at = started_at.isoformat()
                    elif started_at is not None:
                        started_at = str(started_at)

                write_sync_status(
                    warehouse,
                    status="failed",
                    started_at=started_at or utc_now_iso(),
                    completed_at=utc_now_iso(),
                    message=f"Scheduler caught unhandled sync error: {exc}",
                )
        sleep(interval_seconds)


if __name__ == "__main__":
    main()
