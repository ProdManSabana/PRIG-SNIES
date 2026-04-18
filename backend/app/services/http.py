from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class HttpClient:
    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "PRIG-SNIES/1.0 (+https://snies.mineducacion.gov.co/portal/ESTADISTICAS/Bases-consolidadas/)"
                )
            }
        )

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def get_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def download(self, url: str, target_path: Path) -> Path:
        response = self.session.get(url, timeout=self.timeout, stream=True)
        response.raise_for_status()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
        return target_path

