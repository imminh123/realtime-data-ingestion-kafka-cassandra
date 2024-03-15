FROM confluentinc/cp-kafka-connect:latest

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"

RUN confluent-hub install --no-prompt jcustenborder/kafka-connect-spooldir:2.0.65 
RUN confluent-hub install --no-prompt datastax/kafka-connect-cassandra-sink:1.4.0
