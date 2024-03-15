# Part 1 - Batch data ingestion pipeline

## 1. Sample data file configuration & service agreement

### Data File Configuration Schema
Tenants need to specify in detail what data going into **mysimbdp**. As data will be stored in Cassandra, it's important that the Schema is defined beforehand. We chose Avro in this case as this is a popular standard for defining data type. The rest of parameters put some constrains to the type and size of input data as currently **mysimbdp** hasn't grown to adapt to a variety of file types and a large demand for computing resources.
| Parameter | Description |
| --------------- | --------------- |
|   name  | Descriptive name for the data   |
| file_type    | Type of data file    |
| key_space    | Key space of storage (Cassandra)    |
| csv.first.row.as.header    | Flag to treat first line of CSV file as header    |
| schema    | Avro schema (schema.name will be use as table name)    |
| primary_key    | Primary key, following Cassandra documentation    |
| max_file_size_mb    | Set maximum accepted file size    |

### Service Agreement Schema
Here tenants will specify how they want **mysimbdp** to execute **clientbatchingestapp**. For batch processing, client provided program will be executed periodically based on provided **schedule** property, with requested resources.

| Parameter | Description |
| --------------- | --------------- |
|   client  | Unique identifier for client   |
| data_retention_period_days    | Duration for data retention after processing    |
| schedule    | Schedule to run processing task periodically (Kubernetes's convention)    |
| resources    | Explicitly specify resources needed to run client's provided task   

### Sample configuration
### Tenant A
**Data File Configuration**
```
{
  "name": "speed-tracking-data",
  "file_type": "csv",
  "key_space": "mysimbdp_coredms",
  "csv.first.row.as.header": "true",
  "schema": {
    "type": "record",
    "name": "analytics", 
    "fields": [
      { "name": "PROVINCECODE", "type": "string" },
      { "name": "DEVICEID", "type": "string" },
      { "name": "IFINDEX", "type": "int" },
      { "name": "FRAME", "type": "int" },
      { "name": "SLOT", "type": "int" },
      { "name": "PORT", "type": "int" },
      { "name": "ONUINDEX", "type": "int" },
      { "name": "ONUID", "type": "int" },
      { "name": "TIME", "type": "string" },
      { "name": "SPEEDIN", "type": "double" },
      { "name": "SPEEDOUT", "type": "double" }
    ]
  },
  "primary_key": ["PROVINCECODE", "DEVICEID", "ONUID"],
  "max_file_size_mb": 50
}
```

**Service Agreement**
```
{
  "client": "client_a",
  "data_retention_period_days": "7",
  "schedule": "0 * * * *",
  "resources": {
    "requests": {
      "memory": "64Mi",
      "cpu": "250m"
    },
    "limits": {
      "memory": "128Mi",
      "cpu": "500m"
    }
  }
}
```

### Tenant B
```
{
  "name": "amazon-product-review-data",
  "file_type": "csv",
  "key_space": "product_insights",
  "csv.first.row.as.header": "true",
  "schema": {
    "type": "record",
    "name": "product_reviews",
    "fields": [
      {"name": "marketplace", "type": "string"},
      {"name": "customer_id", "type": "string"},
      {"name": "review_id", "type": "string"},
      {"name": "product_id", "type": "string"},
      {"name": "product_parent", "type": "string"},
      {"name": "product_title", "type": "string"},
      {"name": "product_category", "type": "string"},
      {"name": "star_rating", "type": "int"},
      {"name": "helpful_votes", "type": "int"},
      {"name": "total_votes", "type": "int"},
      {"name": "vine", "type": "string"},
      {"name": "verified_purchase", "type": "string"},
      {"name": "review_headline", "type": "string"},
      {"name": "review_body", "type": "string"},
      {"name": "review_date", "type": "string", "logicalType": "date"}
    ]
  },
  "primary_key": ["product_id", "review_id", "customer_id"],
  "max_file_size_mb": 20
}
```

**Service Agreement**
```
{
  "client": "client_b",
  "data_retention_period_days": "3",
  "schedule": "*/1 * * * *",
  "resources": {
    "requests": {
      "memory": "128Mi",
      "cpu": "500m"
    },
    "limits": {
      "memory": "256Mi",
      "cpu": "1Gi"
    }
  }
}
```

## 2. Design of clientbatchingestapp
  
![Design of clientbatchingestapp](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/clientbatchingestapp.png?raw=true)

**As a tenant, there are 2 main components** </br>
1. Client ingestes data file into **client-staging-input-directory** using a set of RESTful API provided by **mysimbdp**.
- **POST: /upload-file/{tenant_id}**: Upload file (Form Data)
- **GET /tenant/{tenant_id}**: Fetch lists of files in **client-staging-input-directory**

2. **clientbatchingestapp** as a Docker image that can be pulled by **mysimbdp**. There are 2 environment variables (provided by **mysimbdp**) that the program need to care about.
- CLIENT_ID: The same value as **client** property in Service Agreement, to uniquely identify tenant.
- SOURCE_PATH: **clientbatchingestapp** will fetch tenant's data from the directory following this format:
  ```
  {SOURCE_PATH}/{CLIENT_ID}/in
  ```

  The processed data (data wrangling) needs to be stored in the directory following this format:
  ```
  {SOURCE_PATH}/{CLIENT_ID}/out
  ```
  
In this case, using Pandas, we've perform `data wrangling` by dropping all rows with NULL values from the DataFrame.

## 3. Design of mysimbdp-batchingestmanager
![Design of mysimbdp-batchingestmanager](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/batchingestmanager.png?raw=true)

**mysimbdp-batchingestmanager** leverages [Kubernetes Cronjob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) to schedule **clientbatchingestapp** performing the ingestion for available files in **client-staging-input-directory**. <br>

Based on provided *service agreement configuration file* provided by tenant, a corresponding Kubernetes `cronjob.yaml` will be created for **batchingestmanager**.

```
apiVersion: batch/v1
kind: CronJob
metadata:
  name: client-batch-ingestion-cron-1
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: client-batch-ingestion-cron
            image: client-batch-ingestion:latest
            imagePullPolicy: Never
            env:
              - name: SOURCE_PATH
                value: "/data"
              - name: CLIENT_ID
                value: "1"
            volumeMounts:
              - name: data-volume
                mountPath: /data
            resources:
              requests:
                memory: "64Mi"
                cpu: "250m"
              limits:
                memory: "128Mi"
                cpu: "500m"
                ...........
```

## 4. Multi-tenancy Model 

![Multi-tenancy Model ](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/ingestion_processor.png?raw=true)

Let's zoom in at the heart of **mysimbdp** platform, the `Ingestion Processor`. 

In order to handle a multi-tenancy model, **batchingestmanager** as a Kubernetes cluster will be shared for all tenants, orchestrating multiple **clientbatchingestapp** instances.

A Kafka Broker will be shared, each **clientbatchingestapp** will use one Topic for data streaming. 

For each tenant, there will be a new Kafka Connect worker. Each worker manages one `Source Connector` (pull data from our staging directory and publish to corresponding Kafka Topic) and one `Sink Connector` (subscribe to Kafka Topic and Ingest data into our **mysimbdp_coredms**).

The **mysimbdp_coredms** cluster which is the platform's data warehouse will be shared, as well as the **client-staging-input-directory** (each tenant will own a sub-directory).

### Implementation

**Performance**: 
With 1 Kafka node, 4 nodes of Cassandra (replication = 2). Batch size (sink) = 32 and batch size (source) = 2000. Our platform is capable of ingesting over 6000 records per minutes.

**Error**
Exception happen when schema configuration provided by client does not adhere to data file constrain, with limited processing power, this cause our **coredms** to crashed after a few seconds.

**Violation of constraints**: the data file constrain has specified the pattern for accepted file `"input.file.pattern": ".*\\.csv$"`. Thus any file that does not match this pattern will be ignore without any log.

```
2024-03-15 12:29:51    statement: INSERT INTO mysimbdp_coredms.analytics(provincecode,deviceid,ifindex,frame,slot,port,onuindex,onuid,time,speedin,speedout) VALUES (:provincecode,:deviceid,:ifindex,:frame,:slot,:port,:onuindex,:onuid,:time,:speedin,:speedout) USING TIMESTAMP :kafka_internal_timestamp} (com.datastax.oss.kafka.sink.CassandraSinkTask)
2024-03-15 12:29:51 [2024-03-15 10:29:51,878] WARN Error inserting/updating row for Kafka record SinkRecord{kafkaOffset=300156, timestampType=CreateTime, originalTopic=locations, originalKafkaPartition=0, originalKafkaOffset=300156} ConnectRecord{topic='locations', kafkaPartition=0, key=Struct{}, keySchema=Schema{com.github.jcustenborder.kafka.connect.model.Key:STRUCT}, value=Struct{PROVINCECODE=HKD,DEVICEID=2222771642618,IFINDEX=6828878457269,FRAME=1,SLOT=1,PORT=13,ONUINDEX=6,ONUID=222277164261810113006,TIME=01/08/2019 11:38:33,SPEEDIN=541783,SPEEDOUT=29639}, valueSchema=Schema{com.github.jcustenborder.kafka.connect.model.Value:STRUCT}, timestamp=1710453148320, headers=ConnectHeaders(headers=[ConnectHeader(key=file.name, value=ONUData-sample_min_1 23.08.58.csv, schema=Schema{STRING}), ConnectHeader(key=file.name.without.extension, value=ONUData-sample_min_1 23.08.58, schema=Schema{STRING}), ConnectHeader(key=file.path, value=/data/input/ONUData-sample_min_1 23.08.58.csv, schema=Schema{STRING}), ConnectHeader(key=file.parent.dir.name, value=input, schema=Schema{STRING}), ConnectHeader(key=file.length, value=48728, schema=Schema{INT32}), ConnectHeader(key=file.offset, value=6, schema=Schema{INT8}), ConnectHeader(key=file.last.modified, value=Thu Mar 14 21:52:27 UTC 2024, schema=Schema{org.apache.kafka.connect.data.Timestamp:INT64}), ConnectHeader(key=file.relative.path, value=ONUData-sample_min_1 23.08.58.csv, schema=Schema{STRING})])}: All 1 node(s) tried for the query failed (showing first 1 nodes, use getAllErrors() for more): Node(endPoint=cassandra1/192.168.128.6:9042, hostId=93e66b37-98b8-45bc-af26-3773f2b4455e, hashCode=27e50f4f): [com.datastax.oss.driver.api.core.servererrors.UnavailableException: Not enough replicas available for query at consistency LOCAL_ONE (1 required but only 0 alive)]
```


## 5. Logging
As the platform relies on Kafka Connector, which ultilize `log4j` for log configuration. At the momment, our platform collects log by overwriting configuration of `log4j` with our own `/ingestion/connector/config/connect-log4j.properties`.
All logs file will be stored under `/ingestion/logs`.
- `logs/kafka`: Store logs regarding Kafka & Kafka Connect, collect progess of file ingestion, failed, successful operations.
- `logs/cassandra`: Store all DEBUG logs from Cassandra stdout, failed, succeeded operations.

```
code/docker-compose.yaml

      - ./ingestion/connector/config/connect-log4j.properties:/etc/kafka/connect-log4j.properties
      - ./ingestion/logs/kafka:/var/log/kafka
      - ./ingestion/logs/cassandra:/var/log/cassandra
```

As the logs are unstructured data, our platform need to have a dedicate logic component, could be another pipeline to pre-process those data before it can be used for any insight.

---

# Part 2 - Near real-time data ingestion

## 1. Multi-tenancy Model 
![Multi-tenancy Model ](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/clientstreamingestapp.png?raw=true)

All components to support the multi-tenancy model for the near real-time data ingestion capabilities of **mysimpbdp** is the same with our previous system in **Part 1**.

> The core data ingestion processor of **mysimpbdp** rely on shared Kafka broker and dedicated Kafka connect worker for each tenant.

The only difference that support near real-time ingestion is the **streamingestmanager** will handle streaming app in a different way. We'll discuss this in the next question.

## 2. streamingestmanager & clientstreamingestapp
 **clientstreamingestapp** as a Docker image that can be pulled by **mysimbdp**. There are 2 environment variables (provided by **mysimbdp**) that the program need to care about.
  - CLIENT_ID: The same value as **client** property in Service Agreement, to uniquely identify tenant.
  - SOURCE_PATH: **clientbatchingestapp** will fetch tenant's data from the directory following this format:
    ```
    {SOURCE_PATH}/{CLIENT_ID}/in
    ```

    The processed data (data wrangling) needs to be stored in the directory following this format:
    ```
    {SOURCE_PATH}/{CLIENT_ID}/out
    ```

The way **clientstreamingestapp** and **clientbatchingestapp** handling data files shares a lot in common. However, there is one MAJOR difference.
**streamingestmanager** will orchestrate **clientstreamingestapp** as a constant running instance ([Kubernetes Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)), instead of CronJob running with schedule like **clientbatchingestapp**. <br>

Thus **clientstreamingestapp** need to watch the CHANGE in `{SOURCE_PATH}/{CLIENT_ID}/in` directory, using whatever technique that the chosen language capable of. (For example [watchdog](https://pypi.org/project/watchdog/) in Python is a powerful library for observing file changes).


## 3. Develop & test
The program that take data as input and perform data wrangling for streaming app is the exact same as batch ingestion app. Thus, the performance, error, log, and exception are similar. <br>

In this case, using Pandas, we've perform `data wrangling` by dropping all rows with NULL values from the DataFrame.

## 4. Report
This can refer to answer 3.1 on how our platform can implement a mechanism for client app to report its metric, including components, flows and the mechanism for reporting. <br>

As clientstreamingestapp is implemented by client, it's important that we must have a clear, structured format of report, or any logging produced. <br>
A sample structured
```
{
  "start": "2024-03-15T11:00:00Z",
  "end": "2024-03-15T12:00:00Z",
  "average_time": 0.05,
  "total_data_size": 2048,
  "number_of_records": 600000
}
```
## 5. Alert & Scalling
Unfortunately there's not enough time for me to implement this. However, the way I would do this is to setup a cronjob to periodically fetch new report files from client, and base on the content, giving instruction to **streamingestmanager** to scale up/down our instance for **clientstreamingestapp**.
It would be easier to leverage feature of cloud providers. For example with AWS, we can use Cloud Watch alert to trigger EC2 auto scalling group, notify admin or trigger an action in EKS.

# Part 3 - Integration and Extension 
## 1. Logging and Monitoring
![Multi-tenancy Model](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/logging.png?raw=true)

In this architecture, there are several key components:
1. Log exporter <br>
  Depend on the source, we will have different log exporter. For client provided application, there can be a constrain of where to store the custom log file. For Kafka Connect, depend on the connector provider, there are different level of supporting monitoring. Kafka can also be monitor with JMX.
  For example: we are using `DataStax Apache Kafka™ Connector` which has clear [documentation](https://docs.datastax.com/en/kafka/doc/kafka/kafkaConfigureLogging.html) on how to enabling the log exporter.

2. Log collector <br>
  This component is reponsible for collecting all the logs exported by all other component. Besides having custom logic for each service, we can rely on tools like [Prometheus](https://prometheus.io/) to set up scape task periodically, and alert manager.

3. Analytic Engine & Analytic Dashboard<br>
  This is another data ingestion pipeline that will take data from **Log collector** and distribute to other **analytic services**.
  For example: Data can go to [Big Query](https://cloud.google.com/bigquery?hl=en) for BI task, and to monitoring tools like [New Relic](https://newrelic.com/) for overal health/performance monitoring, distributed tracing, etc.


## 2. Multiple sinks
The complexity depends on how much freedom, customization we as platform provider want to provide to tenants. <br>
The current architecture relies on Kafka Connector and its ecosystem of plugin (Ex: [Confluent Hub](https://www.confluent.io/hub/)). Our platform can benefit from this ecosystem by integrating a variety of popular Kafka Connector Plugins, such as:
- JDBC Source and Sink Connector
- Google BigQuery Sink Connector
- Amazon S3 Sink Connector
- HDFS 2 Sink Connector
- MySQL Source Connector

Thus gave tenants more configuration options in **Service Agreement** for ingesting data to more than one sink.

## 3. Encryption
Encryption is a tricky part, our platform can support File-level encryption and off load the key management to 3rd party cloud provider like AWS for key rotation and storage. <br>

As the data goes into **coredms** need to have pre-defined structures, it's quite complicated if we relies on client to do the encryption task. This should be handled on our platform, and controlled only by flag in client configuration file. Data in **client-staging-input-directory** can stay encrypted but the trade-off will be performance and cost as we need more resources to handle encrypt/decrypt files.

## 4. Data quality controlled
There can be extra logic in our platform to handle data quality control by a pre-defined set of rules. Several criterias can include:
- Completeness: make sure there's no incomplete records or missing values.
- Validity: make sure data adhere to rules explicitly defined in **Service Agreement** and supported by our platform.
- Timeliness: make sure ingested data is up-to-date and relevant to the business.

This mean an extra step in our pipeline as we should not rely on Kafka Connector to support this kind of data quality checking before ingestion. This logic/component will stay in between the client provided application and the ingestion manager.

## 5. Multiple clientbatchingestapp.
As our platform relies on Kubernetes to orchestrate client task, which alreay come with features support allocating resources, and dealing with different workloads (auto scaling). Our job as a platform provider is to abstract these features into configurable settings to clients, and interprets it into Kubernetes configuration files.

