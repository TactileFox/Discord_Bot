Write-Output "Starting FastAPI app..."
uvicorn main:app --host 127.0.0.1 --port 8000 --reload