def validate_reconciliation(
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    monthly_counts: dict
):

    accounted_rows = (
        valid_rows +
        invalid_rows
    )

    if total_rows != accounted_rows:

        raise RuntimeError(
            "Source reconciliation failed. "
            f"total_rows={total_rows}, "
            f"valid_rows={valid_rows}, "
            f"invalid_rows={invalid_rows}"
        )

    partition_total = sum(
        monthly_counts.values()
    )

    if partition_total != valid_rows:

        raise RuntimeError(
            "Partition reconciliation failed. "
            f"valid_rows={valid_rows}, "
            f"partition_rows={partition_total}"
        )

    return True