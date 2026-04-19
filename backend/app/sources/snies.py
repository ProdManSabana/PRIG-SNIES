from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.core.settings import Settings
from app.models.domain import DatasetProfile
from app.services.http import HttpClient


@dataclass(slots=True)
class SourceAsset:
    source: str
    year: int
    profile: str
    title: str
    url: str | None
    local_path: Path | None = None


SNIES_TITLES: dict[DatasetProfile, str] = {
    DatasetProfile.INSCRITOS: "Estudiantes Inscritos {year}",
    DatasetProfile.ADMITIDOS: "Estudiantes Admitidos {year}",
    DatasetProfile.MATRICULADOS: "Estudiantes Matriculados {year}",
    DatasetProfile.MATRICULADOS_PRIMER_CURSO: "Estudiantes Matriculados en primer curso {year}",
    DatasetProfile.GRADUADOS: "Estudiantes Graduados {year}",
    DatasetProfile.DOCENTES: "Docentes {year}",
    DatasetProfile.METADATOS: "Metadatos bases consolidadas {year}",
}


class SniesSource:
    def __init__(self, settings: Settings, client: HttpClient) -> None:
        self.settings = settings
        self.client = client

    def discover_assets(self) -> list[SourceAsset]:
        html = self.client.get_text(self.settings.snies_base_url)
        soup = BeautifulSoup(html, "html.parser")
        base_href = soup.find("base")
        resolution_base = base_href.get("href") if base_href and base_href.get("href") else self.settings.snies_base_url
        anchors = {anchor.get_text(" ", strip=True).casefold(): anchor.get("href") for anchor in soup.find_all("a")}

        assets: list[SourceAsset] = []
        for year in self.settings.target_years:
            for profile, template in SNIES_TITLES.items():
                title = template.format(year=year)
                raw_href = anchors.get(title.casefold())
                url = urljoin(resolution_base, raw_href) if raw_href else None
                assets.append(
                    SourceAsset(
                        source="snies",
                        year=year,
                        profile=profile.value,
                        title=title,
                        url=url,
                    )
                )
        return assets

    def download_assets(self, assets: list[SourceAsset]) -> list[SourceAsset]:
        downloaded: list[SourceAsset] = []
        for asset in assets:
            if not asset.url:
                downloaded.append(asset)
                continue
            suffix = Path(urlparse(asset.url).path).suffix or ".bin"
            filename = f"{asset.year}_{asset.profile}{suffix}"
            target = self.settings.landing_dir / "snies" / str(asset.year) / filename
            try:
                asset.local_path = self.client.download(asset.url, target)
            except Exception:
                asset.local_path = None
            downloaded.append(asset)
        return downloaded
