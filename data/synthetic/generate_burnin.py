import random
from pathlib import Path

import pandas as pd


RANDOM_SEED = 42
NUM_COMPONENTS = 1000


def generate_component(component_id: int) -> dict:
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
        mu=10.0,
        sigma=0.8,
    )

    noise_24h = random.gauss(0, 0.2)
    noise_96h = random.gauss(0, 0.3)
    noise_168h = random.gauss(0, 0.4)

    if defect_type == "healthy":
        drift_per_hour = random.uniform(
            -0.002,
            0.004,
        )

    elif defect_type == "mild_drift":
        drift_per_hour = random.uniform(
            0.01,
            0.025,
        )

    elif defect_type == "strong_drift":
        drift_per_hour = random.uniform(
            0.03,
            0.07,
        )

    else:
        drift_per_hour = random.uniform(
            0.005,
            0.015,
        )

    leakage_0h = baseline

    leakage_24h = (
        baseline
        + drift_per_hour * 24
        + noise_24h
    )

    leakage_96h = (
        baseline
        + drift_per_hour * 96
        + noise_96h
    )

    leakage_168h = (
        baseline
        + drift_per_hour * 168
        + noise_168h
    )

    if defect_type == "latent_defect":
        late_acceleration = random.uniform(
            8.0,
            20.0,
        )

        leakage_168h += late_acceleration

    return {
        "component_id": f"C{component_id:04d}",
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

    records = [
        generate_component(i)
        for i in range(1, num_components + 1)
    ]

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