from fastapi import FastAPI

# Create FastAPI application
app = FastAPI(
    title="Spectra API",
    version="0.1.0",
    description="AI-powered data analytics platform backend",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Spectra API is running"}
