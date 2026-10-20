from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import uvicorn
import os
from pathlib import Path
import shutil

app = FastAPI(title="Recon Engine Pro")

# Serve frontend
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

# Ensure outputs directory
output_dir = Path(__file__).parent / "outputs"
output_dir.mkdir(exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return FileResponse(frontend_dir / "index.html")

@app.post("/reconcile")
async def reconcile(
    bank_file: UploadFile = File(...),
    invoice_file: UploadFile = File(...),
    threshold: int = 75,
    tolerance: float = 0.05,
):
    try:
        from recon_engine import process_reconciliation
        result = process_reconciliation(
            bank_file.file,
            invoice_file.file,
            threshold=threshold,
            amount_tolerance=tolerance,
        )
        summary = result.get("summary", {})
        pdf_name = summary.get("pdf_file") or result.get("pdf_file")
        csv_name = summary.get("csv_file") or result.get("csv_file")
        return {
            "summary": summary,
            "pdf_url": f"/download/{pdf_name}" if pdf_name else None,
            "csv_url": f"/download/{csv_name}" if csv_name else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
def download(filename: str):
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "application/pdf" if filename.endswith(".pdf") else "text/csv"
    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)

@app.post("/clear-db")
def clear_db():
    try:
        # Clear outputs directory
        for f in output_dir.glob("*"):
            if f.is_file():
                f.unlink()
        # Clear SQLite databases if any
        db_path = Path(__file__).parent / "recon_data.db"
        if db_path.exists():
            db_path.unlink()
        return {"ok": True, "message": "Database cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
