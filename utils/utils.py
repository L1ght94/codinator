import os
import pickle

path_to_pickle = os.environ['SNIPPETS_FILE']
os.makedirs(os.path.dirname(path_to_pickle), exist_ok=True)

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

def extract_code_snippet(output_str: str) -> str:
    try:
        return f"```{output_str.split('```')[1]}```"
    except:
        raise Exception("Could not get code snippet")