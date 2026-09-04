INSERT INTO `{project_id}.{audit_dataset}.{audit_table}`
(
    batch_id,
    pipeline_type,
    process_date,
    year,
    month,
    file_name,
    status,
    rows_processed,
    message
)

VALUES
(
    @batch_id,
    @pipeline_type,
    CURRENT_TIMESTAMP(),
    @year,
    @month,
    @file_name,
    @status,
    @rows_processed,
    @message
)
