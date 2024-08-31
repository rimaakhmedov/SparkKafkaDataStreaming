import logging

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType




def create_keyspace(session):
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS spark_streaming
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """)

    print("Keyspace created successfully!")


def create_table(session):
    session.execute("""
    CREATE TABLE IF NOT EXISTS spark_streaming.users (
        full_name text primary key, gender text, country text, city text, address text, email text);
    """)

    print("Table created successfully!")


def insert_data(session, **kwargs):
    print("inserting data...")

    full_name = kwargs.get('full_name')
    gender = kwargs.get('gender')
    country = kwargs.get('country')
    city = kwargs.get('city')
    address = kwargs.get('address')
    email = kwargs.get('email')

    try:
        session.execute("""
            INSERT INTO spark_streams.created_users(full_name, gender, country, 
                city, address, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, gender, country,
              city, address, email))
        logging.info(f"Data inserted for {full_name}")

    except Exception as e:
        logging.error(f'could not insert data due to {e}')


def create_spark_connection():
    s_conn = None

    try:
        s_conn = SparkSession.builder \
            .appName("SparkDataStreaming") \
            .config("spark.jars.packages",
                    "com.datastax.spark:spark-cassandra-connector-assembly_2.12:3.5.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2,org.apache.kafka:kafka-clients:3.7.0") \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.cassandra.auth.username", "cassandra") \
            .config("spark.cassandra.auth.password", "cassandra") \
            .getOrCreate()

        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn


def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        spark_df = spark_conn.readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', 'localhost:9092') \
            .option('subscribe', 'users') \
            .option('startingOffsets', 'earliest') \
            .load()
        logging.info("kafka dataframe created successfully")
    except Exception as e:
        logging.warning(f"kafka dataframe could not be created because: {e}")

    return spark_df




def create_cassandra_connection(host, port, username, password):
    try:
        auth_provider = PlainTextAuthProvider(username, password)
        cluster = Cluster([host], port=port, auth_provider=auth_provider)

        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create cassandra connection due to {e}")
        return None


def create_selection_df_from_kafka(spark_df):
    schema = StructType([
        StructField("full_name", StringType(), False),
        StructField("gender", StringType(), False),
        StructField("country", StringType(), False),
        StructField("city", StringType(), False),
        StructField("address", StringType(), False),
        StructField("email", StringType(), False)
    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")
    print(sel)

    return sel


CASSANDRA_HOST = 'cassandra'
CASSANDRA_PORT = 9042
CASSANDRA_USERNAME = 'cassandra'
CASSANDRA_PASSWORD = 'cassandra'


if __name__ == "__main__":
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)
        session = create_cassandra_connection(CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_USERNAME, CASSANDRA_PASSWORD)

        if session is not None:
            create_keyspace(session)
            create_table(session)

            logging.info("Streaming is being started...")

            streaming_query = (selection_df.writeStream.format("org.apache.spark.sql.cassandra")
                               .option('checkpointLocation', '/tmp/checkpoint')
                               .option('keyspace', 'spark_streaming')
                               .option('table', 'users')
                               .start())

            streaming_query.awaitTermination()

