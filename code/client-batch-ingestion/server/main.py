import argparse
from confluent_kafka import Producer
import pandas as pd
import datetime
import json
import os


def datetime_converter(dt):
    if isinstance(dt, datetime.datetime):
        return dt.__str__()


# Params required for each tenants
# source_path = "/Users/nguyenminh/Documents/Project/Aalto/BigDataPlatform/data_ingestion_kafka/client-batch-ingestion/server/data/1/in"

source_path = os.getenv("SOURCE_PATH", "/Users/nguyenminh/Documents/Project/Aalto/BigDataPlatform/data_ingestion_kafka/client-batch-ingestion/server/data")
client_id = os.getenv("CLIENT_ID", "1")

"""
The following code emulates the situation that we have real time data to be sent to kafka
"""
if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", help="Input file")
    parser.add_argument("-c", "--chunksize", help="chunk size for big file")
    parser.add_argument("-s", "--sleeptime", help="sleep time in second")
    args = parser.parse_args()

    chunksize = 10
    sleeptime = 1
    """
    Because the KPI file is big, we emulate by reading chunk, using iterator and chunksize
    """

    file_name_paths = []
    print("---- Starting the process -----")
    print(source_path)
    print(f"{source_path}/{client_id}/in")

    for root, dirs_list, files_list in os.walk(
       f"{source_path}"
    ):
        for file_name in files_list:
            print("Processing files_list ", file_name)
        for dirs_list in files_list:
            print("Processing dirs_list ", file_name)
            

    for root, dirs_list, files_list in os.walk(
       f"{source_path}/{client_id}/in"
    ):
        for file_name in files_list:
            print("Processing file ", file_name)
            if os.path.splitext(file_name)[-1] == ".csv":
                file_name_path = os.path.join(root, file_name)
                file_name_paths.append(file_name_path)

    for file_path in file_name_paths:
        destination = f"{source_path}/{client_id}/out"
        print("Destination ", destination)
        print("File path ", file_path)
        if(not os.path.exists(destination)):   
            os.makedirs(destination, exist_ok=True)

        input_data = pd.read_csv(
            file_path, parse_dates=["TIME"], iterator=True, chunksize=chunksize
        )

        write_header = True
        for chunk_data in input_data:
            """
            process each chunk
            """

            # handling data wrangling
            # filtered_chunk_data = chunk_data[['PROVINCECODE']]
            filtered_chunk_data = chunk_data
            chunk = filtered_chunk_data.dropna()
            
            chunk.to_csv(f"{destination}/{os.path.basename(file_path)}", mode='a', header=write_header, index=False)
            print("Write to CSV ", f"{destination}/{os.path.basename(file_path)}")
            write_header = False

    print("---- Exit the process -----")