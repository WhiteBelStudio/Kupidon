from fastapi import FastAPI

app = FastAPI(title="KUPIDON Health")

@app.get("/")
async def health():
    return {"status": "ok", "version": "0.3.0"}
