import random
import ast
import json
import re
import streamlit as st

def string_to_list(s):
    if not s:
        st.error("Error: Received empty response from model.")
        st.stop()
    s = s.strip()
    # Strip markdown code blocks if present
    s = re.sub(r"^```(?:python|json)?\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\s*```$", "", s, flags=re.MULTILINE)
    s = s.strip()
    # Strip variable assignment e.g. quiz = [...]
    if "=" in s and not s.startswith("["):
        s = s.split("=", 1)[1].strip()
    try:
        return ast.literal_eval(s)
    except Exception:
        pass
    # Extract bracketed list
    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end != -1 and end > start:
        sub = s[start:end+1]
        try:
            return ast.literal_eval(sub)
        except Exception:
            try:
                return json.loads(sub)
            except Exception:
                pass
    st.error("Error: The generated quiz was not in the expected format. Please try again.")
    st.stop()

def get_randomized_options(options):
    opts = list(options)
    correct_answer = opts[0]
    random.shuffle(opts)
    return opts, correct_answer
