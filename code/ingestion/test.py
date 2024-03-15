import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f'File {event.src_path} has been modified')
        if event.is_directory:
            return
        print(f'File {event.src_path} has been modified')

    def on_created(self, event):
        if event.is_directory:
            return
        print(f'File {event.src_path} has been created')

    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f'File {event.src_path} has been deleted')

if __name__ == "__main__":
    path = '/Users/nguyenminh/Documents/Project/Aalto/BigDataPlatform/data_ingestion_kafka/ingestion/data/finished/ONUData-sample_min_1.csv' 
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        print(f'Watching directory: {path}')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
