from openai import OpenAI

client = OpenAI()
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List
import os

from models.models import Snippet, Feedback
from utils import utils

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Serve static files, assuming your HTML, CSS, JS are in a directory named 'static'
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open('static/design.html', 'r') as f:
        return f.read()


snippets = utils.load_pkl()
languages = ['Python', 'Javascript', 'Ruby', 'C', 'Java']


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def get_openai_model():
    return os.getenv("OPENAI_MODEL")


@app.get("/languages/")
async def get_list_of_languages():
    return languages


@app.post("/snippets/", response_model=Snippet)
async def create_snippet(snippet: Snippet, api_key: str = Depends(get_openai_api_key), model=Depends(get_openai_model)):
    ids = [s.id for s in snippets]
    if ids:
        snippet.id = max(ids) + 1
    else:
        snippet.id = 1
 
    snippet.description = utils.sanitize_input(snippet.description)
    try:
        message = {
            "role": "user",
            "content": f"### {snippet.language}\n{snippet.description}\n###"
        }
        openai_response = client.chat.completions.create(
            model=model,
            messages=[message],
            max_tokens=150
        )
        code = openai_response.choices[0].message.content.strip()
        snippet.code = utils.extract_code_snippet(code)
        assistant_response = {"role": "assistant", "content": snippet.code}

        snippet.previous_messages.extend([message, assistant_response])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    snippets.append(snippet)
    utils.update_pkl(snippets)
    return snippet


@app.get("/snippets/", response_model=List[Snippet])
async def list_snippets():
    return snippets


@app.get("/snippets/{snippet_id}", response_model=List[Snippet])
async def list_snippets(snippet_id: int):
    return [snippet for snippet in snippets if snippet.id == snippet_id]


@app.delete("/snippets/{snippet_id}")
async def delete_snippet(snippet_id: int):
    global snippets
    snippets = [snippet for snippet in snippets if snippet.id != snippet_id]
    utils.update_pkl(snippets)
    return {"message": "Snippet deleted successfully"}


@app.post("/snippets/{snippet_id}/feedback", response_model=Snippet)
async def modify_snippet(snippet_id: int, feedback: Feedback, api_key: str = Depends(get_openai_api_key), model: str = Depends(get_openai_model)):
    for i, snippet in enumerate(snippets):
        if snippet.id == snippet_id:
            break

    feedback.message = utils.sanitize_input(feedback.message)
    try:
        new_message = {
            "role": "user",
            "content": f"### {feedback.message}\n###"
        }
        messages = snippet.previous_messages + [new_message]
        openai_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=150
        )
        code = openai_response.choices[0].message.content.strip()
        snippet.code = utils.extract_code_snippet(code)
        snippet.previous_messages.extend([messages, snippet.code])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    snippets[i] = snippet
    utils.update_pkl(snippets)
    return snippet


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
