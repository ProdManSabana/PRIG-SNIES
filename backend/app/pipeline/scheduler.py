from time import sleep

from app.core.settings import get_settings
from app.pipeline.sync import run_sync


def main() -> None:
    settings = get_settings()
    interval_seconds = max(settings.sync_interval_hours, 1) * 3600
    while True:
        try:
            run_sync()
        except Exception:
            pass
        sleep(interval_seconds)


if __name__ == "__main__":
    main()
