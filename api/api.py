import uvicorn
from fastapi import FastAPI, File, Query, UploadFile, Form
from rag.retriever import get_answer
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import os
from PyPDF2 import PdfReader
from typing import IO, Optional
import re


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_BASE_URL = os.getenv("STATIC_BASE_URL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("DB_URL environment variable missing")


@app.post("/ask")
async def ask_gpt(
    question: str = Form(...),
    history: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    try:
        chat_history = convert_string_to_history(history)
        q = question
        if file:
            content = extract_text_from_pdf(file.file)
            chat_history.append(("User:", content))
            if not question:
                q = "Apibendrink tokį el. receptą ir pateik vaisto alternatyvas pagal veikliąją medžiagą"
        print(q, flush=True)
        print(chat_history, flush=True)
        response = get_answer(q, chat_history)
        return {"question": q, "answer": response}
    except Exception as e:
        return {"error": str(e)}


@app.get('/')
def index():
    return {'message': 'Welcome to MedicineAI Chatbot'}


def extract_text_from_pdf(file: IO[bytes]) -> str:
    """
    Extracts text from a PDF file object using PyPDF2.

    :param file: A file-like object containing a PDF
    :return: Extracted text as a single string.
    """
    reader = PdfReader(file)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    full_text = "\n".join(text)
    # Remove patient and specialist sections
    text_no_patient = remove_section_between(full_text, "Pacientas:", "Sveikatos priežiūros įstaigos specialistas:")
    final_text = remove_section_between(text_no_patient, "Sveikatos priežiūros įstaigos specialistas:", "Informacija pacientui:")

    return final_text


def remove_section_between(text: str, start_marker: str, end_marker: str) -> str:
    """
    Removes all lines between start_marker and end_marker (inclusive of start, exclusive of end).
    """
    pattern = rf'{re.escape(start_marker)}\n(?:.*\n)*?(?={re.escape(end_marker)})'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text


def convert_string_to_history(log_string):
    # Regex to find "User:" or "AI:" and split into (role, message) chunks
    pattern = re.compile(r"(User:|AI:)", re.IGNORECASE)
    parts = pattern.split(log_string)
    parts = [p.strip() for p in parts if p.strip()]  # remove empty parts

    history = []
    last_user = None

    i = 0
    while i < len(parts) - 1:
        role = parts[i].lower()
        message = parts[i + 1].strip()
        if role == "user:":
            last_user = message
        elif role == "ai:":
            if last_user is not None:
                history.append((last_user, message))
                last_user = None
        i += 2

    return history
