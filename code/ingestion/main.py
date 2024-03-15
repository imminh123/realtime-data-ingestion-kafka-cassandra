from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kafka_bootstrap import kafka_bootstrap
from cassandra_bootstrap import cassandra_bootstrap, create_cassandra_table
import os

app = FastAPI()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# client need to provide this
schema = {
    "type": "record",
    "name": "analytics",
    "fields": [
        {"name": "PROVINCECODE", "type": "string"},
        {"name": "DEVICEID", "type": "string"},
        {"name": "IFINDEX", "type": "string"},
        {"name": "FRAME", "type": "string"},
        {"name": "SLOT", "type": "string"},
        {"name": "PORT", "type": "string"},
        {"name": "ONUINDEX", "type": "string"},
        {"name": "ONUID", "type": "string"},
        {"name": "TIME", "type": "string"},
        {"name": "SPEEDIN", "type": "string"},
        {"name": "SPEEDOUT", "type": "string"},
    ],
}

primary_key = ["PROVINCECODE", "DEVICEID", "ONUID"]

async def on_startup():
    # await cassandra_bootstrap()
    await create_cassandra_table(
        schema, keyspace="mysimbdp_coredms", primary_key=primary_key
    )
    await kafka_bootstrap()


app.add_event_handler("startup", on_startup)


# Directory to save the uploaded files
UPLOAD_DIR = "client-staging-input-directory"


@app.get("/tenant/{tenant_id}")
def read_root(tenant_id: str):

    # Create the directory if it doesn't exist
    upload_dir = f"{UPLOAD_DIR}/{tenant_id}/in"
    if(not os.path.exists(upload_dir)):
        os.makedirs(upload_dir, exist_ok=True)

    files = os.listdir(f"{UPLOAD_DIR}/{tenant_id}/in")
    return files


@app.post("/upload-file/{tenant_id}")
async def create_upload_file(tenant_id: str, file: UploadFile = File(...)):
    try:
        upload_dir = f"{UPLOAD_DIR}/{tenant_id}/in"
        file_path = os.path.join(upload_dir, file.filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        return JSONResponse(
            content={"message": "File uploaded successfully", "file_path": file_path}
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
