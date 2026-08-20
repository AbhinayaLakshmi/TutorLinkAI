from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.modules.onboarding.routes import auth_router, onboarding_router

app = FastAPI(
    title="TutorLinkAI Onboarding API",
    description="API services for User, Student and Tutor Onboarding",
    version="1.0.0"
)

# CORS Middleware setup
# Allows development frontend (on http://localhost:5173 or similar) to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(onboarding_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "TutorLinkAI Onboarding Service"
    }
