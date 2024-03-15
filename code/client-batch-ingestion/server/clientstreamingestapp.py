from confluent_kafka import Producer
import pandas as pd
import datetime
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def datetime_converter(dt):
    if isinstance(dt, datetime.datetime):
        return dt.__str__()


source_path = os.getenv(
    "SOURCE_PATH",
    "/Users/nguyenminh/Documents/Project/Aalto/BigDataPlatform/data_ingestion_kafka/client-batch-ingestion/server/data",
)
client_id = os.getenv("CLIENT_ID", "1")

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"File {event.src_path} has been modified")

        chunksize = 10
        file_name_paths = []
        print("---- Starting the process -----")
        print(source_path)
        print(f"{source_path}/{client_id}/in")

        for root, files_list in os.walk(f"{source_path}"):
            for file_name in files_list:
                print("Processing files_list ", file_name)

        for root, files_list in os.walk(f"{source_path}/{client_id}/in"):
            for file_name in files_list:
                print("Processing file ", file_name)
                if os.path.splitext(file_name)[-1] == ".csv":
                    file_name_path = os.path.join(root, file_name)
                    file_name_paths.append(file_name_path)

        for file_path in file_name_paths:
            destination = f"{source_path}/{client_id}/out"
            print("Destination ", destination)
            print("File path ", file_path)
            if not os.path.exists(destination):
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

                chunk.to_csv(
                    f"{destination}/{os.path.basename(file_path)}",
                    mode="a",
                    header=write_header,
                    index=False,
                )
                print("Write to CSV ", f"{destination}/{os.path.basename(file_path)}")
                write_header = False

            if event.is_directory:
                return


"""
The following code emulates the situation that we have real time data to be sent to kafka
"""
if __name__ == "__main__":
    path = f"{source_path}/{client_id}/in"
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        print(f"Watching directory: {path}")
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("---- Exit the process -----")
