FROM apache/airflow:2.7.1-python3.10

COPY pyproject.toml /opt/airflow/

RUN pip install --upgrade pip \
 && pip install .