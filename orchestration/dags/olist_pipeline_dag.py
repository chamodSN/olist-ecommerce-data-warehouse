from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

import os

default_args = {
    "owner": "olist_dw",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["chamodnethminaprofessional@gmail.com"],
}


def _run_ingestion():
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    from src.ingestion.upload_to_bronze import main as ingestion_main
    ingestion_main()


def _run_data_quality_checks():
    import sys
    sys.path.insert(0, "/opt/airflow/project/data_quality")
    from run_all_checks import main as dq_main
    dq_main()


def _make_transform_callable(entity_name: str):
    def _run():
        import sys
        sys.path.insert(
            0, "/opt/airflow/project/transformation/bronze_to_silver")
        module = __import__(f"transform_{entity_name}", fromlist=[
                            f"transform_{entity_name}"])
        getattr(module, f"transform_{entity_name}")()
    return _run


with DAG(
    dag_id="olist_data_warehouse_pipeline",
    default_args=default_args,
    description="Bronze ingestion -> DQ gate -> Silver transform -> Gold dbt build",
    schedule_interval="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["olist", "data-warehouse"],
) as dag:

    ingest_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=_run_ingestion,
    )

    run_data_quality_checks = PythonOperator(
        task_id="run_data_quality_checks",
        python_callable=_run_data_quality_checks,
    )

    transform_entities = [
        "customers", "geolocation", "orders", "order_items",
        "order_payments", "order_reviews", "products", "sellers",
    ]

    transform_tasks = [
        PythonOperator(
            task_id=f"transform_{entity}",
            python_callable=_make_transform_callable(entity),
        )
        for entity in transform_entities
    ]

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/project/transformation/dbt_project/olist_dbt && "
            "/opt/dbt_venv/bin/dbt run --profiles-dir ."
        ),
        env={**os.environ, "REDSHIFT_PASSWORD": "{{ conn.redshift_olist_dw.password }}"},
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/project/transformation/dbt_project/olist_dbt && "
            "/opt/dbt_venv/bin/dbt test --profiles-dir ."
        ),
        env={**os.environ, "REDSHIFT_PASSWORD": "{{ conn.redshift_olist_dw.password }}"},
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    ingest_bronze >> run_data_quality_checks >> transform_tasks >> dbt_run >> dbt_test
