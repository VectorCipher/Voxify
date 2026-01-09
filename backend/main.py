from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from llm_chain import get_llm_chain
from data.student_loader import get_student

import whisper
import os
import uuid
import re
from openai import OpenAI


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)



whisper_model = whisper.load_model("small")
llm_chain = get_llm_chain()
openai_client = OpenAI()



def split_sentences(text: str):
    # Clean + safe sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]


@app.post("/upload-audio")
async def upload_and_transcribe(audio: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    audio_path = os.path.join(UPLOAD_DIR, f"{file_id}.webm")

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    
    whisper_result = whisper_model.transcribe(audio_path)
    user_text = whisper_result["text"]

    
    student = get_student(user_text)

    if student:
        student_context = f"""
Student Name: {student['name']}
Class: {student['class']}
Roll No: {student['roll_no']}

Marks:
Physics: {student['subjects']['Physics']}
Chemistry: {student['subjects']['Chemistry']}
Mathematics: {student['subjects']['Mathematics']}
Biology: {student['subjects']['Biology']}
Hindi: {student['subjects']['Hindi']}
English: {student['subjects']['English']}

Teacher Suggestion:
{student['teacher_suggestion']}
"""
    else:
        student_context = "No matching student record found."

    
    answer_msg = llm_chain.invoke({
        "question": f"""
Parent Question:
{user_text}

Student Report Card Data:
{student_context}

Instructions:
- Answer like a school teacher
- Be polite and reassuring
- Do not invent any data
"""
    })

    return {
        "user_text": user_text,
        "answer": answer_msg.content
    }

@app.websocket("/ws/tts")
async def tts_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            
            text = await websocket.receive_text()

            sentences = split_sentences(text)

            for sentence in sentences:
                styled_text = f"{sentence}"

                with openai_client.audio.speech.with_streaming_response.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    input=styled_text
                ) as response:
                    for chunk in response.iter_bytes():
                        await websocket.send_bytes(chunk)

                
                await websocket.send_text("__SENTENCE__")
            
            
            await websocket.send_text("__END__")

    except Exception as e:
        print("WebSocket closed:", e)
