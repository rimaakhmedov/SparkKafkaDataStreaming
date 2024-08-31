from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


dag = DAG(
    'kafka_stream_dag',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': days_ago(1),
        'retries': 1,
    },
    schedule_interval=None,
    catchup=False,
)


run_kafka_stream = BashOperator(
    task_id='run_kafka_stream',
    bash_command='python app/from_api_to_kafka.py',
    dag=dag,
)

run_kafka_stream
