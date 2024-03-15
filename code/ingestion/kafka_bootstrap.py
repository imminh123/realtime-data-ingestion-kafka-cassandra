from confluent_kafka.admin import AdminClient, NewTopic


async def kafka_bootstrap():
    # Specify the Kafka broker(s) as a list of bootstrap servers
    bootstrap_servers = "localhost:19092"

    # Create an AdminClient instance
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

    # Specify the topic name and other configuration options

    num_partitions = 1
    replication_factor = 1
    config = {"cleanup.policy": "compact"}

    topics = ["test_topic", "quickstart-config", "quickstart-status", "quickstart-offsets"]

    kafka_topics = [
        NewTopic(
            topic=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            config=config,
        )
        for topic_name in topics
    ]

    # Create the topic using the create_topics method
    fs = admin_client.create_topics(kafka_topics)

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


    