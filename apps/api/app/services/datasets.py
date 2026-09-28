from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SYNTHETIC_DATASET_ID = "synthetic-burnin"
DATASET_PATH = REPOSITORY_ROOT / "data/synthetic/burnin_dataset.csv"
OBSERVATION_COLUMNS = [
    "component_id", "lot_id", "leakage_0h", "leakage_24h",
]


class SelectionNotFound(ValueError):
    pass


class DatasetUnavailable(RuntimeError):
    pass


class DatasetRepository:
    """Read a fresh snapshot of the single supported demonstration dataset."""

    def __init__(self, path: Path = DATASET_PATH):
        self.path = path

    def load(self, dataset_id: str) -> pd.DataFrame:
        if dataset_id != SYNTHETIC_DATASET_ID:
            raise SelectionNotFound(f"Dataset '{dataset_id}' was not found.")
        try:
            dataset = pd.read_csv(
                self.path, dtype={"component_id": str, "lot_id": str},
            )
            if not set(OBSERVATION_COLUMNS).issubset(dataset.columns):
                raise ValueError("Required dataset columns are missing.")
            if dataset[["component_id", "lot_id"]].isna().any().any():
                raise ValueError("Dataset identities are missing.")
            if dataset["component_id"].duplicated().any():
                raise ValueError("Duplicate component identities.")
            # Keep missing measurements as None for existing Data Forensics.
            for column in ("leakage_0h", "leakage_24h"):
                dataset[column] = pd.to_numeric(dataset[column], errors="raise")
            return dataset.astype(object).where(pd.notna(dataset), None)
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            raise DatasetUnavailable("Synthetic dataset is unavailable or invalid.") from exc

    @staticmethod
    def component(dataset: pd.DataFrame, component_id: str) -> dict:
        rows = dataset.loc[dataset["component_id"] == component_id]
        if rows.empty:
            raise SelectionNotFound(f"Component '{component_id}' was not found.")
        return rows.iloc[0][OBSERVATION_COLUMNS].to_dict()

    def list_components(
        self, dataset_id: str, search: str, page: int, page_size: int,
    ) -> dict:
        dataset = self.load(dataset_id)
        search = search.strip()
        if search:
            dataset = dataset.loc[
                dataset["component_id"].str.contains(search, case=False, regex=False)
                | dataset["lot_id"].str.contains(search, case=False, regex=False)
            ]
        dataset = dataset.sort_values("component_id", kind="stable")
        start = (page - 1) * page_size
        return {
            "dataset_id": dataset_id,
            "items": dataset.iloc[start:start + page_size][OBSERVATION_COLUMNS].to_dict("records"),
            "total": len(dataset),
            "page": page,
            "page_size": page_size,
        }


def get_dataset_repository() -> DatasetRepository:
    return DatasetRepository()
