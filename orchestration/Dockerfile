FROM apache/airflow:2.9.3

COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt" \
    -r /requirements-airflow.txt

USER root
RUN python3 -m venv /opt/dbt_venv && \
    /opt/dbt_venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/dbt_venv/bin/pip install --no-cache-dir dbt-redshift
USER airflow