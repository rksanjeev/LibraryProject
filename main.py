import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.router import v1_router
from services.smtpd import SMTPConsoleServer
import uvicorn


app = FastAPI()
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include the API router
app.include_router(v1_router)




if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    # Host and port configuration
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    # Start the SMTP console server
    smtp_server = SMTPConsoleServer()
    smtp_server.start()

    # Run the FastAPI application
    uvicorn.run(app, host=host, port=port)





