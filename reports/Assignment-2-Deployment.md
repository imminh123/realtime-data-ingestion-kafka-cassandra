# This is a deployment/installation guide

### Deploy Cassandra Cluster
This file is reused from Assignment 1 <br>

The docker compose located in `code/docker-compose-cassandra.yaml`
```
docker-compose -f docker-compose-cassandra.yaml up -d
```

### Setting up Cassandra Keyspace
Run FastAPI server, update `data_constrain` variable if you want to use other data files.
```
python code/ingestion/main.py
```

### Build local image for Kafka Connect packed with connectors
Dockerfile locates in `ingestion/connector/csv`

```
docker build -t kafka-connect-bdp:1.0.0 . 
```

### Deploy Kafka & Kafka Connect Cluster
```
docker-compose up -d
```

Sending GET request to this url to verified we have 2 connectors installed , http://localhost:8083/connectors

```
[
"cassandra-sink",
"csv-spooldir-connector"
]
```

### Start Minikube (for local environment): `minikube start`

By now, our system looks like this from the container point of view
![system](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/docker.jpg?raw=true)


### Register Connector to Kafka Connect
csv-spooldir-connector
```
curl --location 'http://localhost:8083/connectors' \
--header 'Content-Type: application/json' \
--data '{
  "name": "csv-spooldir-connector",
  "config": {
    "tasks.max": "1",
    "connector.class": "com.github.jcustenborder.kafka.connect.spooldir.SpoolDirCsvSourceConnector",
    "input.path": "/data/input",
    "input.file.pattern": ".*\\.csv$",
    "schema.generation.enabled": "true",
    "error.path": "/data/error",
    "finished.path": "/data/finished",
    "halt.on.error": "false",
    "topic": "locations",
    "csv.first.row.as.header": "true"
  }
}
'
```

cassandra-sink
```
curl --location 'http://localhost:8083/connectors' \
--header 'Content-Type: application/json' \
--data '{
    "name": "cassandra-sink",
    "config": {
        "connector.class": "com.datastax.oss.kafka.sink.CassandraSinkConnector",
        "tasks.max": "1",
        "topics": "locations",
        "contactPoints": "cassandra1",
        "loadBalancing.localDc": "helsinki",
        "port": 9042,
        "ignoreErrors": "None",
        "maxConcurrentRequests": 500,
        "maxNumberOfRecordsInBatch": 32,
        "queryExecutionTimeout": 30,
        "connectionPoolLocalSize": 4,
        "jmx": true,
        "compression": "None",

        "auth.provider": "None",
        
        "topic.locations.mysimbdp_coredms.analytics.mapping": "marketplace=value.marketplace,customer_id=value.customer_id,review_id=value.review_id,product_id=value.product_id,product_parent=value.product_parent,product_title=value.product_title,product_category=value.product_category,star_rating=value.star_rating,helpful_votes=value.helpful_votes,total_votes=value.total_votes,vine=value.vine, verified_purchase=value.verified_purchase, review_headline=value.review_headline, review_body=value.review_body, review_date=value.review_date",
        "topic.locations.mysimbdp_coredms.analytics.consistencyLevel": "LOCAL_ONE",
        "topic.locations.mysimbdp_coredms.analytics.ttl": -1,
        "topic.locations.mysimbdp_coredms.analytics.ttlTimeUnit" : "SECONDS",
        "topic.locations.mysimbdp_coredms.analytics.timestampTimeUnit" : "MICROSECONDS",
        "topic.locations.mysimbdp_coredms.analytics.nullToUnset": "true",
        "topic.locations.mysimbdp_coredms.analytics.deletesEnabled": "true",
        "topic.locations.codec.locale": "en_US",
        "topic.locations.codec.timeZone": "UTC",
        "topic.locations.codec.timestamp": "CQL_TIMESTAMP",
        "topic.locations.codec.date": "ISO_LOCAL_DATE",
        "topic.locations.codec.time": "ISO_LOCAL_TIME",
        "topic.locations.codec.unit": "MILLISECONDS"
    }
}
'
```

### Build local image for client ingest application 
Dockerfile locates in `code/client-batch-ingestion/server/Dockerfile`

1. Change docker daemon to use Minikube docker daemon
`eval $(minikube docker-env)` 
2. Build images 
```
docker build -t client-batch-ingestion:latest . 
```

We have both sample `clientbatchingestapp` and `clientstreamingestapp`, make changes to Dockerfile to choose one, default `clientbatchingestapp`
```
# CMD ["python", "clientstreamingestapp.py"]
CMD ["python", "clientbatchingestapp.py"]
```

### Mount Minikube volume to host system
`minikube mount ${HOME}/code/ingestion/client-staging-input-directory:/data/client-staging-input-directory`

### Applying clientbatchingesapp
`kubectl apply -f code/bdp-k8s/cronjob.yaml `

### (Or) Applying clientstreamingestapp
`code/bdp-k8s/deployment.yaml`

### Optional
I have a simple client web interface to showcase the use of REST API to put data files into `client-staging-input-directory`. 
The program is located in `code/client-batch-ingestion/client`.
```
npm run dev
```

![system](https://github.com/imminh123/realtime-data-ingestion-kafka-cassandra/blob/main/assets/sample_client_web_ui.jpg?raw=true)






