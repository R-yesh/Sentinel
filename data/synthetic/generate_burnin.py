import random
from pathlib import Path

import pandas as pd


RANDOM_SEED = 42
NUM_COMPONENTS = 1000
LOT_SIZE = 50
LOT_BASELINE_SIGMA = 0.4

def generate_component(
    component_id: int,
    lot_id: str,
    lot_baseline: float,
    ) -> dict:
    defect_type = random.choices(
        population=[
            "healthy",
            "mild_drift",
            "strong_drift",
            "latent_defect",
        ],
        weights=[
            0.70,
            0.15,
            0.10,
            0.05,
        ],
        k=1,
    )[0]

    baseline = random.gauss(
        mu=lot_baseline,
        sigma=0.6,
    )

    noise_24h = random.gauss(0, 0.2)
    noise_96h = random.gauss(0, 0.3)
    noise_168h = random.gauss(0, 0.4)

    if defect_type == "healthy":
        drift_per_hour = random.uniform(
            -0.002,
            0.004,
        )
        instability = 0.0

    elif defect_type == "mild_drift":
        drift_per_hour = random.uniform(
            0.01,
            0.025,
        )
        instability = 0.0

    elif defect_type == "strong_drift":
        drift_per_hour = random.uniform(
            0.03,
            0.07,
        )
        instability = 0.0

    else:
        drift_per_hour = random.uniform(
            0.005,
            0.015,
        )
        instability = random.uniform(
            0.4,
            1.0,
        )

    leakage_0h = baseline

    leakage_24h = (
        baseline
        + drift_per_hour * 24
        + instability * 0.8
        + noise_24h
    )

    leakage_96h = (
        baseline
        + drift_per_hour * 96
        + instability * 3.0
        + noise_96h
    )

    leakage_168h = (
        baseline
        + drift_per_hour * 168
        + instability * 12.0
        + noise_168h
    )

    return {
        "component_id": f"C{component_id:04d}",
        "lot_id": lot_id,
        "defect_type": defect_type,
        "leakage_0h": leakage_0h,
        "leakage_24h": leakage_24h,
        "leakage_96h": leakage_96h,
        "leakage_168h": leakage_168h,
    }


def generate_dataset(
    num_components: int = NUM_COMPONENTS,
) -> pd.DataFrame:
    random.seed(RANDOM_SEED)

    num_lots = (
        num_components + LOT_SIZE - 1
    ) // LOT_SIZE

    lot_baselines = {
        lot_number: random.gauss(
            mu=10.0,
            sigma=LOT_BASELINE_SIGMA,
        )
        for lot_number in range(
            1,
            num_lots + 1,
        )
    }

    records = []

    for component_id in range(
        1,
        num_components + 1,
    ):
        lot_number = (
            (component_id - 1) // LOT_SIZE
        ) + 1

        lot_id = f"LOT-{lot_number:03d}"

        record = generate_component(
            component_id=component_id,
            lot_id=lot_id,
            lot_baseline=lot_baselines[
                lot_number
            ],
        )

        records.append(record)

    return pd.DataFrame(records)


def main():
    dataset = generate_dataset()

    output_path = Path(
        "data/synthetic/burnin_dataset.csv"
    )

    dataset.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Generated {len(dataset)} components."
    )

    print(
        dataset["defect_type"].value_counts()
    )

    print(
        f"Saved dataset to {output_path}"
    )


if __name__ == "__main__":
    main()