from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from app.settings import Settings
from app.routers import users, sets
from app.sql.database import Base, engine
from app.models import Result

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title='Flashcard API')


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(Result(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY, message='JSON validation error'))
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(sets.router)

app.mount(Settings.STATIC_PATH, StaticFiles(
    directory='app/static'), name='static')


@app.get('/', include_in_schema=False)
def root():
    return HTMLResponse(content='See /docs for API documentation', status_code=400)
