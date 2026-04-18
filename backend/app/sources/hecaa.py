from pathlib import Path

import pandas as pd

from app.core.settings import Settings
from app.services.http import HttpClient
from app.services.normalization import clean_dataframe, to_snake_case


class HecaaSource:
    def __init__(self, settings: Settings, client: HttpClient) -> None:
        self.settings = settings
        self.client = client

    def fetch_institutions(self) -> Path:
        html = self.client.get_text(self.settings.hecaa_ies_url)
        tables = pd.read_html(html)
        candidate = max(tables, key=lambda frame: len(frame.columns))
        candidate.columns = [to_snake_case(column) for column in candidate.columns]
        candidate = clean_dataframe(candidate)
        target = self.settings.raw_dir / "hecaa" / "institutions.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        candidate.to_csv(target, index=False)
        return target

