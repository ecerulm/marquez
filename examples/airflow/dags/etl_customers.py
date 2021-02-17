from marquez_airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.sensors import ExternalTaskSensor
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'datascience',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'email': ['datascience@example.com']
}

dag = DAG(
    'etl_customers',
    schedule_interval='@once',
    catchup=False,
    is_paused_upon_creation=False,
    default_args=default_args,
    description='Loads newly registered customers daily.'
)

# Wait for new_food_deliveries DAG to complete
t1 = ExternalTaskSensor(
    task_id='wait_for_new_food_deliveries',
    external_dag_id='new_food_deliveries',
    mode='reschedule',
    dag=dag
)

t2 = PostgresOperator(
    task_id='if_not_exists',
    postgres_conn_id='food_delivery_db',
    sql='''
    CREATE TABLE IF NOT EXISTS customers (
      id         SERIAL PRIMARY KEY,
      created_at TIMESTAMP NOT NULL,
      updated_at TIMESTAMP NOT NULL,
      name       VARCHAR(64) NOT NULL,
      email      VARCHAR(64) UNIQUE NOT NULL,
      address    VARCHAR(64) NOT NULL,
      phone      VARCHAR(64) NOT NULL,
      city_id    INTEGER REFERENCES cities(id)
    );''',
    dag=dag
)

t3 = PostgresOperator(
    task_id='etl',
    postgres_conn_id='food_delivery_db',
    sql='''
    INSERT INTO customers (id, created_at, updated_at, name, email, address, phone, city_id)
      SELECT id, created_at, updated_at, name, email, address, phone, city_id
        FROM tmp_customers;
    ''',
    dag=dag
)

t1 >> t2 >> t3
