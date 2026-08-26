data-migration/
│
├── README.md
├── .gitignore
├── requirements.txt
├── .env.example
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── source_reader.py
│   │   ├── extractor.py
│   │   └── config.py
│   │
│   ├── incremental/
│   │   ├── __init__.py
│   │   ├── incremental_loader.py
│   │   └── watermark.py
│   │
│   ├── transform/
│   │   ├── __init__.py
│   │   │
│   │   ├── bronze/
│   │   │   ├── __init__.py
│   │   │   └── load_bronze.py
│   │   │
│   │   ├── silver/
│   │   │   ├── __init__.py
│   │   │   └── transform_silver.py
│   │   │
│   │   └── gold/
│   │       ├── __init__.py
│   │       └── transform_gold.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── schema_validation.py
│   │   ├── row_count_validation.py
│   │   ├── data_quality.py
│   │   └── reconciliation.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── config.py
│       └── exceptions.py
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── versions.tf
│   ├── backend.tf
│   │
│   ├── bigquery/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── buckets/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── service_account/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_incremental.py
│   ├── test_transform.py
│   └── test_validation.py
│
├── config/
│   ├── dev.yaml
│   └── prod.yaml
│
└── scripts/
    ├── setup.sh
    ├── run_migration.sh
    └── validate.sh