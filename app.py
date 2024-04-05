import glob
import hashlib
import json
import os

import pandas as pd
import streamlit as st

from openai_extractor import extract_data


def hash_file(filename):
    h = hashlib.sha1()
    with open(filename, "rb") as file:
        chunk = 0
        while chunk != b"":
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()


DOCS_FOLDER = "/Users/zoltanctoth/My Google Drive/Számlák/Rendezetlen papirok"
STATE = "state.json"

if __name__ == "__main__":

    if os.path.exists(STATE):
        with open(STATE, "r") as f:
            state = json.load(f)
    else:
        state = {}

    df = pd.DataFrame()
    files = glob.glob(f"{DOCS_FOLDER}/*.pdf", recursive=True)
    for f in files:
        if os.path.isfile(f):
            file_hash = hash_file(f)
            base_name = os.path.basename(f)
            if file_hash not in state:
                state[file_hash] = {"path": f}
            if "attrs" not in state[file_hash]:
                response = extract_data(f)
                state[file_hash]["attrs_raw"] = response
                with open(STATE, "w") as f:
                    json.dump(state, f)
                try:
                    state[file_hash]["attrs"] = json.loads(response)
                except Exception:
                    state[file_hash]["attrs"] = {"error": "Error parsing response"}
                    print(response)
                with open(STATE, "w") as f:
                    json.dump(state, f)

            if "date" not in state[file_hash]["attrs"]:
                state[file_hash]["attrs"]["date"] = ""

            target_date = (
                state[file_hash]["attrs"]["completion_date"]
                if "completion_date" in state[file_hash]["attrs"]
                else (
                    state[file_hash]["attrs"]["date"]
                    if "date" in state[file_hash]["attrs"]
                    else ""
                )
            )
            df = df._append(
                {
                    "file_name": base_name,
                    "path": f,
                    "target_date": target_date,
                },
                ignore_index=True,
            )

    display_df = df.copy()
    display_df["month"] = display_df["target_date"]
    st.data_editor(
        display_df,
        column_config={
            "path": st.column_config.TextColumn(
                label="File",
                disabled=True,
            ),
            "date": st.column_config.TextColumn(),
        },
    )  # Same as st.write(df)
