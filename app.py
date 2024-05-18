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


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open('static/design.html', 'r') as f:
        return f.read()


snippets: List[Snippet] = utils.load_pkl()
languages = eval(os.environ['PG_LANGUAGES'])
max_tokens = int(os.environ['MAX_TOKENS'])


@app.get("/languages/")
async def get_list_of_languages():
    return languages

@app.post("/snippets", response_model=Snippet)
async def create_snippet(snippet: Snippet):
    global snippets
    ids = [s.id for s in snippets]
    if ids:
        new_id = max(ids) + 1
    else:
        new_id = 1

    new_snippet = Snippet(
        id=new_id,
        language=snippet.language,
        description=snippet.description,
        code=snippet.code,
        feedback=snippet.feedback,
        previous_messages=snippet.previous_messages,
        tests=snippet.tests,
        test_case_history=snippet.test_case_history,
        test_result=snippet.test_result
    )

    snippets.insert(0, new_snippet)
    utils.update_pkl(snippets)
    return new_snippet


@app.post("/snippets/{snippet_id}/generate_code", response_model=Snippet)
async def generate_code(snippet: Snippet, snippet_id: int, api_key: str = Depends(utils.get_openai_api_key), model=Depends(utils.get_openai_model)):
    global snippets

    for lang in utils.find_languages(snippet.description):
        snippet.description = snippet.description.replace(lang, "")

    snippet.description = utils.sanitize_input(snippet.description)
    try:
        message = {
            "role": "user",
            "content": f"### write the code in {snippet.language} with following\
                         description\n{snippet.description}\n###"
        }
        openai_response = client.chat.completions.create(
            model=model,
            messages=[message],
            max_tokens=max_tokens
        )
        code = openai_response.choices[0].message.content.strip()
        code = utils.extract_code_snippet(code)
        snippet.code = code.replace(snippet.language.lower(), "").strip()
        snippet.id = snippet_id
        assistant_response = {"role": "assistant", "content": snippet.code}

        snippet.previous_messages.extend([message, assistant_response])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for i, s in enumerate(snippets):
        if s.id == snippet.id:
            break
    snippets[i] = snippet
    utils.update_pkl(snippets)
    return snippet


@app.get("/snippets", response_model=List[Snippet])
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


@app.post("/snippets/{snippet_id}/improve_code", response_model=Snippet)
async def improve_code(snippet_id: int, feedback: Feedback, api_key: str = Depends(utils.get_openai_api_key), model: str = Depends(utils.get_openai_model)):
    global snippets
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
            max_tokens=max_tokens
        )
        code = openai_response.choices[0].message.content.strip()

        snippet.code = utils.extract_code_snippet(code)
        assistant_response = {"role": "assistant", "content": snippet.code}
        snippet.previous_messages.extend([new_message, assistant_response])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    snippets[i] = snippet
    utils.update_pkl(snippets)
    return snippet


@app.post("/snippets/{snippet_id}/generate_tests", response_model=Snippet)
def generate_test_cases(snippet_id: int, api_key: str = Depends(utils.get_openai_api_key), model=Depends(utils.get_openai_model)):
    global snippets
    for i, snippet in enumerate(snippets):
        if snippet.id == snippet_id:
            break

    try:
        new_message = {
            "role": "user",
            "content": f"### Generate test cases\n###"
        }
        messages = [{"role": "assistant", "content": snippet.code}, new_message]

        openai_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )

        tests = openai_response.choices[0].message.content.strip()
        tests = tests.replace(snippet.language.lower(), "").strip()
        snippet.tests = utils.extract_code_snippet(tests)
        assistant_response = {"role": "assistant", "content": snippet.tests}

        snippet.test_case_history.extend([new_message, assistant_response])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    snippets[i] = snippet
    utils.update_pkl(snippets)

    return snippet


@app.post("/snippets/{snippet_id}/improve_tests", response_model=Snippet)
async def improve_tests(snippet_id: int, feedback: Feedback, api_key: str = Depends(utils.get_openai_api_key), model: str = Depends(utils.get_openai_model)):
    global snippets
    for i, snippet in enumerate(snippets):
        if snippet.id == snippet_id:
            break

    feedback.message = utils.sanitize_input(feedback.message)
    try:
        new_message = {
            "role": "user",
            "content": f"### {feedback.message}\n###"
        }
        messages = snippet.test_case_history + [new_message]
        openai_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        code = openai_response.choices[0].message.content.strip()
        snippet.tests = utils.extract_code_snippet(code)

        assistant_response = {"role": "assistant", "content": snippet.tests}
        snippet.test_case_history.extend([new_message, assistant_response])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    snippets[i] = snippet
    utils.update_pkl(snippets)
    return snippet


@app.post("/snippets/{snippet_id}/run_tests", response_model=Snippet)
def run_test_code(snippet_id: int, api_key: str = Depends(utils.get_openai_api_key), model=Depends(utils.get_openai_model)):
    global snippets
    for i, snippet in enumerate(snippets):
        if snippet.id == snippet_id:
            break

    try:
        new_message = {
            "role": "user",
            "content": f"### Run the test cases against the code and tell me if\
                         all of them passed in a single word: yes or no\n###"
        }
        messages = [{"role": "assistant", "content": snippet.code}, new_message]

        openai_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        result = openai_response.choices[0].message.content.strip()

        snippet.test_result = "OK" if 'yes' in result.lower() else "NG"

        return snippet

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
