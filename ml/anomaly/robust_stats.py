from statistics import median


def median_absolute_deviation(values: list[float]) -> float:
    if not values:
        raise ValueError("values cannot be empty")

    med = median(values)

    absolute_deviations = [
        abs(value - med)
        for value in values
    ]

    return median(absolute_deviations)


def robust_z_score(
    value: float,
    population: list[float],
) -> float:
    if not population:
        raise ValueError("population cannot be empty")

    med = median(population)
    mad = median_absolute_deviation(population)

    if mad == 0:
        if value == med:
            return 0.0

        return float("inf")

    return 0.6745 * (value - med) / mad


def percentile_rank(
    value: float,
    population: list[float],
) -> float:
    if not population:
        raise ValueError("population cannot be empty")

    below_or_equal = sum(
        1
        for item in population
        if item <= value
    )

    return below_or_equal / len(population)