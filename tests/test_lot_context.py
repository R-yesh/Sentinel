import pandas as pd
import pytest

from shared.context.lot_context import build_lot_context


def make_dataset():
    return pd.DataFrame(
        [
            {
                "component_id": "C0001",
                "lot_id": "LOT-001",
                "leakage_24h": 10.0,
            },
            {
                "component_id": "C0002",
                "lot_id": "LOT-001",
                "leakage_24h": 10.2,
            },
            {
                "component_id": "C0003",
                "lot_id": "LOT-001",
                "leakage_24h": 10.4,
            },
            {
                "component_id": "C0004",
                "lot_id": "LOT-002",
                "leakage_24h": 11.5,
            },
        ]
    )


def test_build_lot_context():
    dataset = make_dataset()

    context = build_lot_context(
        dataset=dataset,
        component_id="C0002",
    )

    assert context.lot_id == "LOT-001"

    assert context.component_ids == [
        "C0001",
        "C0003",
    ]

    assert context.leakage_24h_population == [
        10.0,
        10.4,
    ]


def test_target_component_is_excluded():
    dataset = make_dataset()

    context = build_lot_context(
        dataset=dataset,
        component_id="C0002",
    )

    assert "C0002" not in context.component_ids

    assert len(context.component_ids) == 2
    assert len(context.leakage_24h_population) == 2


def test_unknown_component_fails():
    dataset = make_dataset()

    with pytest.raises(
        ValueError,
        match="was not found",
    ):
        build_lot_context(
            dataset=dataset,
            component_id="C9999",
        )


def test_component_without_peers_fails():
    dataset = make_dataset()

    with pytest.raises(
        ValueError,
        match="No peer components found",
    ):
        build_lot_context(
            dataset=dataset,
            component_id="C0004",
        )