import os
import pickle
import openai

path_to_pickle = os.environ['SNIPPETS_FILE']
os.makedirs(os.path.dirname(path_to_pickle), exist_ok=True)

def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def get_openai_model():
    return os.getenv("OPENAI_MODEL")


def get_headers():
    headers = {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json"
    }
    return headers

def load_pkl():
    if not os.path.isfile(path_to_pickle):
        return []

    with open(path_to_pickle, 'rb') as pklfile:
        return pickle.load(pklfile)

def update_pkl(snippets):
    with open(path_to_pickle, 'wb') as pklfile:
        pickle.dump(snippets, pklfile)

def sanitize_input(input_string: str) -> str:
    return input_string.replace(";", ".").replace("&", "and")

def find_languages(text: str) -> list[str]:
    messsage = {
        "role": "user",
        "content": f"""Extract the names of the programming languages from the
        following text:\n\n{text}"""
    }
    
    response = openai.chat.completions.create(
        model=get_openai_model(),
        messages=[messsage],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0
    )

    languages = response.choices[0].message.content.strip().split(',')
    languages = [language.strip() for language in languages]

    return languages

def extract_code_snippet(output_str: str) -> str:
    try:
        if '```' in output_str:
            output_str = f"{output_str.split('```')[1]}"
        return output_str
    except:
        raise Exception("Could not get code snippet")