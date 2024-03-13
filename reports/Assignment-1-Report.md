# Part 1 - Batch data ingestion pipeline

## Sample data file configuration & service agreement

### Data File Configuration Schema
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
| Parameter | Description |
| --------------- | --------------- |
|   client  | Unique identifier for client   |
| data_retention_period_days    | Duration for data retention after processing    |
| schedule    | Schedule to run processing task periodically (Kubernetes's convention)    |
| resources    | Explicitly specify resources needed to run client's provided task   

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





