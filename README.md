# SparkKafkaDataStreaming
![](https://github.com/rimaakhmedov/SparkKafkaDataStreaming/blob/main/arch.jpg)

## Apache Airflow
Для запуска Airflow, выполните команду:
```
docker-compose -f docker-compose-LocalExecutor.yml up -d 
```
## Apache Kafka
По адресу localhost:8082 в Kafka UI создайте кластер и топик users.
Для отправки данных в топик users, запустите stream_dag в Airflow по адресу localhost:8080.
## Apache Spark
Для отпраки данных в Cassandra с помощью Spark, сначала копируем spark_stream.py в контейнер:
```
docker cp spark_stream.py spark-master:/opt/bitnami/spark/
```
Далее нужно будет скачать jar файлы в jars директории:
```
docker exec -it spark-master /bin/bash
```
```cd jars
curl -O https://repo1.maven.org/maven2/com/datastax/spark/spark-cassandra-connector-assembly_2.12/3.5.0/spark-cassandra-connector-assembly_2.12-3.5.0.jar
curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.2/spark-sql-kafka-0-10_2.12-3.5.2.jar
curl -O https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.7.0/kafka-clients-3.7.0.jar
```
После отправки данных в Kafka топик можно будет получить их через Spark:
```
cd ..
spark-submit --master local[2] spark_stream.py
```
