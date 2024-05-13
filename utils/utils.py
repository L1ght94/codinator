import os
import pickle

path_to_pickle = os.environ['SNIPPETS_FILE']

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

def sanitize_input(input_string):
    return input_string.replace(";", ".").replace("&", "and")