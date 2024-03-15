from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement


async def cassandra_bootstrap(avro_schema):
    # Replace these with your Cassandra cluster information
    contact_points = ["127.0.0.1"]
    table_name = "analytics"

    # Create a connection to the Cassandra cluster
    cluster = Cluster(contact_points=contact_points, port=9042)

    # Create a session
    session = cluster.connect()

    # Create the keyspace
    command = "CREATE KEYSPACE IF NOT EXISTS mysimbdp_coredms WITH REPLICATION = {'class': 'NetworkTopologyStrategy', 'helsinki' : 2, 'tokyo' : 1 };"

    prepared_statement = session.prepare(command)
    session.execute(prepared_statement)

    # create table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS mysimbdp_coredms.analytics (
        PROVINCECODE TEXT,
        DEVICEID TEXT,
        IFINDEX TEXT,
        FRAME TEXT,
        SLOT TEXT,
        PORT TEXT,
        ONUINDEX TEXT,
        ONUID TEXT,
        TIME TEXT,
        SPEEDIN INT,
        SPEEDOUT INT,
        PRIMARY KEY (PROVINCECODE, DEVICEID, ONUID)
    );
"""

    prepared_statement = session.prepare(create_table_query)
    session.execute(prepared_statement)

    # Close the session and cluster connections
    session.shutdown()
    cluster.shutdown()


async def create_cassandra_table(avro_schema, keyspace, primary_key):
    print(avro_schema)
    # Connect to Cassandra cluster
    cluster = Cluster(["127.0.0.1"])
    session = cluster.connect()

    # Create Keyspace if not exists
    session.execute(
        f"CREATE KEYSPACE IF NOT EXISTS {keyspace} WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}"
    )

    # Switch to the specified keyspace
    session.set_keyspace(keyspace)

    # Create a table based on the Avro schema
    query = (
        f"CREATE TABLE IF NOT EXISTS {avro_schema['name']} {avro_schema_to_cql(avro_schema, primary_key)};"
    )
    session.execute(query)

    # Close the Cassandra session and cluster connection
    session.shutdown()
    cluster.shutdown()


def avro_schema_to_cql(avro_schema, primary_key):
    fields = avro_schema["fields"]
    cql_columns = [
        f'{field["name"]} {avro_type_to_cql(field["type"])}' for field in fields
    ]

    # Add primary key specification
    if primary_key:
        cql_columns.append(f'PRIMARY KEY ({", ".join(primary_key)})')

    return f"({', '.join(cql_columns)})"


def avro_type_to_cql(avro_type):
    if avro_type == "int":
        return "int"
    elif avro_type == "long":
        return "bigint"
    elif avro_type == "double":
        return "double"
    elif avro_type == "string":
        return "text"
    else:
        raise ValueError(f"Unsupported Avro type: {avro_type}")
