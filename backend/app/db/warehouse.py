from contextlib import contextmanager
from time import sleep

import duckdb
import pandas as pd

from app.core.settings import Settings


DUCKDB_LOCK_RETRY_ATTEMPTS = 10
DUCKDB_LOCK_RETRY_DELAY_SECONDS = 1


def should_retry_duckdb_lock(exc: duckdb.IOException) -> bool:
    message = str(exc)
    return "Could not set lock on file" in message and "Conflicting lock is held" in message


class Warehouse:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @contextmanager
    def connect(self, read_only: bool = False):
        connection = None
        last_error = None
        for attempt in range(DUCKDB_LOCK_RETRY_ATTEMPTS):
            try:
                connection = duckdb.connect(str(self.settings.warehouse_path), read_only=read_only)
                break
            except duckdb.IOException as exc:
                last_error = exc
                if not should_retry_duckdb_lock(exc) or attempt == DUCKDB_LOCK_RETRY_ATTEMPTS - 1:
                    raise
                sleep(DUCKDB_LOCK_RETRY_DELAY_SECONDS)

        if connection is None and last_error is not None:
            raise last_error

        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                create table if not exists source_assets (
                    source varchar,
                    year integer,
                    profile varchar,
                    title varchar,
                    url varchar,
                    local_path varchar,
                    status varchar,
                    discovered_at timestamp default current_timestamp
                );
                """
            )
            connection.execute(
                """
                create table if not exists institution_dim (
                    institution_code varchar,
                    institution_name varchar,
                    institution_parent_code varchar,
                    sector varchar,
                    academic_character varchar,
                    domicile_department varchar,
                    domicile_municipality varchar,
                    institution_state varchar,
                    programs_current integer,
                    programs_agreement integer,
                    is_accredited varchar,
                    record_source varchar,
                    loaded_at timestamp default current_timestamp
                );
                """
            )
            connection.execute(
                """
                create table if not exists fact_observations (
                    observation_id varchar primary key,
                    source varchar,
                    year integer,
                    profile varchar,
                    source_file varchar,
                    source_sheet varchar,
                    institution_code varchar,
                    institution_name varchar,
                    department varchar,
                    municipality varchar,
                    measure_value double,
                    dimensions_json varchar,
                    loaded_at timestamp default current_timestamp
                );
                """
            )
            connection.execute(
                """
                create table if not exists observation_dimensions (
                    observation_id varchar,
                    dimension_name varchar,
                    dimension_value varchar
                );
                """
            )
            connection.execute(
                """
                create table if not exists field_metadata (
                    year integer,
                    source_file varchar,
                    sheet_name varchar,
                    row_index integer,
                    metadata_json varchar
                );
                """
            )
            connection.execute(
                """
                create table if not exists sync_status (
                    status varchar,
                    started_at timestamp,
                    completed_at timestamp,
                    message varchar,
                    source_assets integer,
                    downloaded_assets integer,
                    institution_rows integer,
                    observation_rows integer,
                    dimension_rows integer,
                    metadata_rows integer
                );
                """
            )

    def replace_table(self, name: str, frame: pd.DataFrame) -> None:
        with self.connect() as connection:
            connection.register("frame_view", frame)
            connection.execute(f"create or replace table {name} as select * from frame_view")
            connection.unregister("frame_view")

    def query_df(self, sql: str, params: list | None = None) -> pd.DataFrame:
        with self.connect(read_only=True) as connection:
            result = connection.execute(sql, params or []).fetchdf()
        return result

    def execute(self, sql: str, params: list | None = None) -> None:
        with self.connect() as connection:
            connection.execute(sql, params or [])
