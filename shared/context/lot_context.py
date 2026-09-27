import pandas as pd

from shared.schemas.lot import LotContext


def build_lot_context(
    dataset: pd.DataFrame,
    component_id: str,
) -> LotContext:
    component_rows = dataset[
        dataset["component_id"] == component_id
    ]

    if component_rows.empty:
        raise ValueError(
            f"Component '{component_id}' was not found."
        )

    if len(component_rows) > 1:
        raise ValueError(
            f"Duplicate component ID '{component_id}' detected."
        )

    component_row = component_rows.iloc[0]

    lot_id = component_row["lot_id"]

    lot_rows = dataset[
        dataset["lot_id"] == lot_id
    ]

    peer_rows = lot_rows[
        lot_rows["component_id"] != component_id
    ]

    if peer_rows.empty:
        raise ValueError(
            f"No peer components found for lot '{lot_id}'."
        )

    return LotContext(
        lot_id=lot_id,
        component_ids=peer_rows[
            "component_id"
        ].tolist(),
        leakage_0h_population=peer_rows[
            "leakage_0h"
        ].tolist(),
        leakage_24h_population=peer_rows[
            "leakage_24h"
        ].tolist(),
    )