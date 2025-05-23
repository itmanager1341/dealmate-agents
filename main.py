from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Import handler modules
from handlers.run_agent import run_agent_handler
from handlers.transcribe import transcribe_handler
from handlers.parse_xlsx import parse_xlsx_handler
from handlers.memo_draft import memo_draft_handler

app = FastAPI()

# Enable CORS (for frontend calls from Lovable.dev or local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # update with frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run-agent")
async def run_agent(request: Request):
    data = await request.json()
    return await run_agent_handler(data)

@app.post("/transcribe")
async def transcribe(request: Request):
    data = await request.json()
    return await transcribe_handler(data)

@app.post("/parse_xlsx")
async def parse_xlsx(request: Request):
    data = await request.json()
    return await parse_xlsx_handler(data)

@app.post("/memo")
async def memo_draft(request: Request):
    data = await request.json()
    return await memo_draft_handler(data)

@app.get("/")
async def root():
    return {"status": "Dealmate agent backend is running"}

