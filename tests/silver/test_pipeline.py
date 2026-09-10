
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


from src.transform.silver.pipeline import (
    run_silver_pipeline,
)


class FakeClient:
    pass


def make_bronze_df():
    return pd.DataFrame(
        [
            {
                "date": "2024-03-18 09:15:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "symbol": "360ONE",
            }
        ]
    )


def make_valid_df():
    return pd.DataFrame(
        [
            {
                "date": "2024-03-18 09:15:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "symbol": "360ONE",
            }
        ]
    )


def make_silver_df():
    return pd.DataFrame(
        [
            {
                "symbol": "360ONE",
                "timestamp": pd.Timestamp(
                    "2024-03-18 09:15:00"
                ),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
            }
        ]
    )


# ==========================================================
# SUCCESS
# ==========================================================

@patch(
    "src.transform.silver.pipeline.write_audit_record"
)
@patch(
    "src.transform.silver.pipeline.load_silver_data"
)
@patch(
    "src.transform.silver.pipeline.calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline.validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline.read_bronze_data"
)
def test_pipeline_success(
    mock_read,
    mock_validate,
    mock_indicators,
    mock_loader,
    mock_audit,
):
    client = FakeClient()

    mock_read.return_value = make_bronze_df()

    mock_validate.return_value = (
        make_valid_df(),
        pd.DataFrame(),
    )

    mock_indicators.return_value = (
        make_silver_df()
    )

    mock_loader.return_value = 1

    result = run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="HISTORICAL",
        start_date="2024-03-18",
        end_date="2024-03-18",
    )

    assert result["status"] == "SUCCESS"

    assert result["bronze_rows"] == 1
    assert result["validated_rows"] == 1
    assert result["rejected_rows"] == 0
    assert result["silver_rows"] == 1

    mock_read.assert_called_once()

    mock_validate.assert_called_once()

    mock_indicators.assert_called_once()

    mock_loader.assert_called_once()

    mock_audit.assert_called_once()

    audit_kwargs = (
        mock_audit.call_args.kwargs
    )

    assert (
        audit_kwargs["status"]
        == "SUCCESS"
    )

    assert (
        audit_kwargs["bronze_rows"]
        == 1
    )

    assert (
        audit_kwargs["validated_rows"]
        == 1
    )

    assert (
        audit_kwargs["silver_rows"]
        == 1
    )


# ==========================================================
# NO BRONZE DATA
# ==========================================================

@patch(
    "src.transform.silver.pipeline.write_audit_record"
)
@patch(
    "src.transform.silver.pipeline.load_silver_data"
)
@patch(
    "src.transform.silver.pipeline.calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline.validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline.read_bronze_data"
)
def test_pipeline_no_bronze_data(
    mock_read,
    mock_validate,
    mock_indicators,
    mock_loader,
    mock_audit,
):
    client = FakeClient()

    mock_read.return_value = (
        pd.DataFrame()
    )

    result = run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="HISTORICAL",
        start_date="2024-03-18",
        end_date="2024-03-18",
    )

    assert result["status"] == "SUCCESS"

    assert result["bronze_rows"] == 0
    assert result["validated_rows"] == 0
    assert result["rejected_rows"] == 0
    assert result["silver_rows"] == 0

    # Nothing downstream should execute
    mock_validate.assert_not_called()
    mock_indicators.assert_not_called()
    mock_loader.assert_not_called()

    mock_audit.assert_called_once()

    audit_kwargs = (
        mock_audit.call_args.kwargs
    )

    assert (
        audit_kwargs["status"]
        == "SUCCESS"
    )

    assert (
        audit_kwargs["bronze_rows"]
        == 0
    )


# ==========================================================
# VALIDATION FAILURE
# ==========================================================

@patch(
    "src.transform.silver.pipeline.write_audit_record"
)
@patch(
    "src.transform.silver.pipeline.load_silver_data"
)
@patch(
    "src.transform.silver.pipeline.calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline.validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline.read_bronze_data"
)
def test_pipeline_validation_failure(
    mock_read,
    mock_validate,
    mock_indicators,
    mock_loader,
    mock_audit,
):
    client = FakeClient()

    mock_read.return_value = (
        make_bronze_df()
    )

    mock_validate.side_effect = (
        ValueError(
            "Test validation failure"
        )
    )

    with pytest.raises(
        ValueError,
        match="Test validation failure",
    ):
        run_silver_pipeline(
            client=client,
            symbol="360ONE",
            load_type="HISTORICAL",
            start_date="2024-03-18",
            end_date="2024-03-18",
        )

    mock_indicators.assert_not_called()
    mock_loader.assert_not_called()

    mock_audit.assert_called_once()

    audit_kwargs = (
        mock_audit.call_args.kwargs
    )

    assert (
        audit_kwargs["status"]
        == "FAILED"
    )

    assert (
        audit_kwargs["failed_stage"]
        == "validation"
    )

    assert (
        audit_kwargs["error_type"]
        == "ValueError"
    )

    assert (
        "Test validation failure"
        in audit_kwargs[
            "error_message"
        ]
    )


# ==========================================================
# INDICATOR FAILURE
# ==========================================================

@patch(
    "src.transform.silver.pipeline.write_audit_record"
)
@patch(
    "src.transform.silver.pipeline.load_silver_data"
)
@patch(
    "src.transform.silver.pipeline.calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline.validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline.read_bronze_data"
)
def test_pipeline_indicator_failure(
    mock_read,
    mock_validate,
    mock_indicators,
    mock_loader,
    mock_audit,
):
    client = FakeClient()

    mock_read.return_value = (
        make_bronze_df()
    )

    mock_validate.return_value = (
        make_valid_df(),
        pd.DataFrame(),
    )

    mock_indicators.side_effect = (
        RuntimeError(
            "Test indicator failure"
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Test indicator failure",
    ):
        run_silver_pipeline(
            client=client,
            symbol="360ONE",
            load_type="HISTORICAL",
            start_date="2024-03-18",
            end_date="2024-03-18",
        )

    mock_loader.assert_not_called()

    mock_audit.assert_called_once()

    audit_kwargs = (
        mock_audit.call_args.kwargs
    )

    assert (
        audit_kwargs["status"]
        == "FAILED"
    )

    assert (
        audit_kwargs["failed_stage"]
        == "indicators"
    )

    assert (
        audit_kwargs["error_type"]
        == "RuntimeError"
    )


# ==========================================================
# SILVER LOAD FAILURE
# ==========================================================

@patch(
    "src.transform.silver.pipeline.write_audit_record"
)
@patch(
    "src.transform.silver.pipeline.load_silver_data"
)
@patch(
    "src.transform.silver.pipeline.calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline.validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline.read_bronze_data"
)
def test_pipeline_silver_load_failure(
    mock_read,
    mock_validate,
    mock_indicators,
    mock_loader,
    mock_audit,
):
    client = FakeClient()

    mock_read.return_value = (
        make_bronze_df()
    )

    mock_validate.return_value = (
        make_valid_df(),
        pd.DataFrame(),
    )

    mock_indicators.return_value = (
        make_silver_df()
    )

    mock_loader.side_effect = (
        RuntimeError(
            "Test load failure"
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Test load failure",
    ):
        run_silver_pipeline(
            client=client,
            symbol="360ONE",
            load_type="HISTORICAL",
            start_date="2024-03-18",
            end_date="2024-03-18",
        )

    mock_audit.assert_called_once()

    audit_kwargs = (
        mock_audit.call_args.kwargs
    )

    assert (
        audit_kwargs["status"]
        == "FAILED"
    )

    assert (
        audit_kwargs["failed_stage"]
        == "silver_load"
    )

    assert (
        audit_kwargs["error_type"]
        == "RuntimeError"
    )

    assert (
        "Test load failure"
        in audit_kwargs[
            "error_message"
        ]
    )

def test_incremental_requires_start_date():

    client = MagicMock()

    with pytest.raises(
        ValueError,
        match="start_date is required",
    ):

        run_silver_pipeline(
            client=client,
            symbol="360ONE",
            load_type="INCREMENTAL",
            start_date=None,
            end_date="2026-04-09",
        )


def test_incremental_requires_end_date():

    client = MagicMock()

    with pytest.raises(
        ValueError,
        match="end_date is required",
    ):

        run_silver_pipeline(
            client=client,
            symbol="360ONE",
            load_type="INCREMENTAL",
            start_date="2026-04-09",
            end_date=None,
        )


@patch(
    "src.transform.silver.pipeline."
    "write_audit_record"
)
@patch(
    "src.transform.silver.pipeline."
    "load_silver_data"
)
@patch(
    "src.transform.silver.pipeline."
    "calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline."
    "validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline."
    "read_bronze_data"
)
def test_incremental_reads_full_historical_context(
    mock_reader,
    mock_validator,
    mock_indicators,
    mock_loader,
    mock_audit,
):

    client = MagicMock()

    bronze_df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
            ],
            "date": [
                "2026-04-08 15:29:00",
                "2026-04-09 09:15:00",
            ],
            "open": [100, 101],
            "high": [102, 103],
            "low": [99, 100],
            "close": [101, 102],
            "volume": [1000, 1100],
        }
    )

    mock_reader.return_value = (
        bronze_df
    )

    mock_validator.return_value = (
        bronze_df.copy(),
        pd.DataFrame(
            columns=[
                "symbol",
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "failure_reason",
            ]
        ),
    )

    calculated_df = (
        bronze_df
        .rename(
            columns={
                "date": "timestamp"
            }
        )
        .copy()
    )

    mock_indicators.return_value = (
        calculated_df
    )

    mock_loader.return_value = 1

    run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="INCREMENTAL",
        start_date="2026-04-09",
        end_date="2026-04-09",
    )

    mock_reader.assert_called_once_with(
        client=client,
        symbol="360ONE",
        start_date=None,
        end_date="2026-04-09",
    )


@patch(
    "src.transform.silver.pipeline."
    "write_audit_record"
)
@patch(
    "src.transform.silver.pipeline."
    "load_silver_data"
)
@patch(
    "src.transform.silver.pipeline."
    "calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline."
    "validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline."
    "read_bronze_data"
)
def test_incremental_indicators_receive_full_context(
    mock_reader,
    mock_validator,
    mock_indicators,
    mock_loader,
    mock_audit,
):

    client = MagicMock()

    bronze_df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
                "360ONE",
            ],
            "date": [
                pd.Timestamp(
                    "2026-04-08 15:28:00"
                ),
                pd.Timestamp(
                    "2026-04-08 15:29:00"
                ),
                pd.Timestamp(
                    "2026-04-09 09:15:00"
                ),
            ],
            "open": [
                100,
                101,
                102,
            ],
            "high": [
                102,
                103,
                104,
            ],
            "low": [
                99,
                100,
                101,
            ],
            "close": [
                101,
                102,
                103,
            ],
            "volume": [
                1000,
                1100,
                1200,
            ],
        }
    )

    mock_reader.return_value = (
        bronze_df
    )

    mock_validator.return_value = (
        bronze_df.copy(),
        pd.DataFrame(),
    )

    mock_indicators.return_value = (
        pd.DataFrame(
            {
                "symbol": [
                    "360ONE"
                ],
                "timestamp": [
                    pd.Timestamp(
                        "2026-04-09 09:15:00"
                    )
                ],
            }
        )
    )

    mock_loader.return_value = 1

    run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="INCREMENTAL",
        start_date="2026-04-09",
        end_date="2026-04-09",
    )

    passed_df = (
        mock_indicators
        .call_args
        .args[0]
    )

    assert len(
        passed_df
    ) == 3

    assert (
        passed_df["date"].min()
        == pd.Timestamp(
            "2026-04-08 15:28:00"
        )
    )

    assert (
        passed_df["date"].max()
        == pd.Timestamp(
            "2026-04-09 09:15:00"
        )
    )


@patch(
    "src.transform.silver.pipeline."
    "write_audit_record"
)
@patch(
    "src.transform.silver.pipeline."
    "load_silver_data"
)
@patch(
    "src.transform.silver.pipeline."
    "calculate_indicators"
)
@patch(
    "src.transform.silver.pipeline."
    "validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline."
    "read_bronze_data"
)
def test_incremental_loads_only_requested_range(
    mock_reader,
    mock_validator,
    mock_indicators,
    mock_loader,
    mock_audit,
):

    client = MagicMock()

    bronze_df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
                "360ONE",
            ],
            "date": [
                "2026-04-08 15:29:00",
                "2026-04-09 09:15:00",
                "2026-04-09 09:16:00",
            ],
            "open": [
                100,
                101,
                102,
            ],
            "high": [
                102,
                103,
                104,
            ],
            "low": [
                99,
                100,
                101,
            ],
            "close": [
                101,
                102,
                103,
            ],
            "volume": [
                1000,
                1100,
                1200,
            ],
        }
    )

    mock_reader.return_value = (
        bronze_df
    )

    mock_validator.return_value = (
        bronze_df.copy(),
        pd.DataFrame(),
    )

    calculated_df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
                "360ONE",
            ],
            "timestamp": [
                pd.Timestamp(
                    "2026-04-08 15:29:00"
                ),
                pd.Timestamp(
                    "2026-04-09 09:15:00"
                ),
                pd.Timestamp(
                    "2026-04-09 09:16:00"
                ),
            ],
        }
    )

    mock_indicators.return_value = (
        calculated_df
    )

    mock_loader.return_value = 2

    result = run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="INCREMENTAL",
        start_date="2026-04-09",
        end_date="2026-04-09",
    )

    loaded_df = (
        mock_loader
        .call_args
        .kwargs["df"]
    )

    assert len(
        loaded_df
    ) == 2

    assert (
        loaded_df[
            "timestamp"
        ].min()
        == pd.Timestamp(
            "2026-04-09 09:15:00"
        )
    )

    assert (
        loaded_df[
            "timestamp"
        ].max()
        == pd.Timestamp(
            "2026-04-09 09:16:00"
        )
    )

    assert (
        result[
            "silver_rows"
        ]
        == 2
    )


@patch(
    "src.transform.silver.pipeline."
    "write_audit_record"
)
@patch(
    "src.transform.silver.pipeline."
    "load_quarantine_data"
)
@patch(
    "src.transform.silver.pipeline."
    "validate_bronze_data"
)
@patch(
    "src.transform.silver.pipeline."
    "read_bronze_data"
)
def test_incremental_quarantines_only_requested_range(
    mock_reader,
    mock_validator,
    mock_quarantine,
    mock_audit,
):

    client = MagicMock()

    bronze_df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
            ],
            "date": [
                "2026-04-08 10:00:00",
                "2026-04-09 10:00:00",
            ],
            "open": [
                0,
                0,
            ],
            "high": [
                0,
                0,
            ],
            "low": [
                0,
                0,
            ],
            "close": [
                0,
                0,
            ],
            "volume": [
                100,
                100,
            ],
        }
    )

    rejected_df = (
        bronze_df.copy()
    )

    rejected_df[
        "date"
    ] = pd.to_datetime(
        rejected_df[
            "date"
        ]
    )

    rejected_df[
        "failure_reason"
    ] = (
        "NON_POSITIVE_OHLC"
    )

    mock_reader.return_value = (
        bronze_df
    )

    mock_validator.return_value = (
        pd.DataFrame(
            columns=(
                bronze_df.columns
            )
        ),
        rejected_df,
    )

    mock_quarantine.return_value = 1

    result = run_silver_pipeline(
        client=client,
        symbol="360ONE",
        load_type="INCREMENTAL",
        start_date="2026-04-09",
        end_date="2026-04-09",
    )

    quarantine_df = (
        mock_quarantine
        .call_args
        .kwargs[
            "rejected_df"
        ]
    )

    assert len(
        quarantine_df
    ) == 1

    assert (
        quarantine_df
        .iloc[0]["date"]
        == pd.Timestamp(
            "2026-04-09 10:00:00"
        )
    )

    assert (
        result[
            "quarantine_rows"
        ]
        == 1
    )