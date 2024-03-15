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
data_constrain = {
    "name": "speed-tracking-data",
    "supported_file_types": ["csv"],
    "key_space": "mysimbdp_coredms",
    "csv.first.row.as.header": "true",
    "schema": {
        "type": "record",
        "name": "analytics",
        "fields": [
            {"name": "marketplace", "type": "string"},
            {"name": "customer_id", "type": "string"},
            {"name": "review_id", "type": "string"},
            {"name": "product_id", "type": "string"},
            {"name": "product_parent", "type": "string"},
            {"name": "product_title", "type": "string"},
            {"name": "product_category", "type": "string"},
            {"name": "star_rating", "type": "string"},
            {"name": "helpful_votes", "type": "string"},
            {"name": "total_votes", "type": "string"},
            {"name": "vine", "type": "string"},
            {"name": "verified_purchase", "type": "string"},
            {"name": "review_headline", "type": "string"},
            {"name": "review_body", "type": "string"},
            {"name": "review_date", "type": "string"},
        ],
    },
    "primary_key": ["product_id", "customer_id", "review_id"],
    "max_file_size_mb": 50,
}


async def on_startup():
    # await cassandra_bootstrap()
    await create_cassandra_table(
        data_constrain["schema"],
        keyspace="mysimbdp_coredms",
        primary_key=data_constrain["primary_key"],
    )
    await kafka_bootstrap()


app.add_event_handler("startup", on_startup)


# Directory to save the uploaded files
UPLOAD_DIR = "client-staging-input-directory"


@app.get("/tenant/{tenant_id}")
def read_root(tenant_id: str):

    # Create the directory if it doesn't exist
    upload_dir = f"{UPLOAD_DIR}/{tenant_id}/in"
    if not os.path.exists(upload_dir):
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
