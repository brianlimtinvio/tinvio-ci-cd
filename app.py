import webbrowser
import base64
import os
from enum import Enum
from io import BytesIO, StringIO
from typing import Iterator, Optional, Sequence, Tuple, Union, cast
from google.cloud import documentai
import imageio as iio
import pandas as pd
import streamlit as st
import streamlit.components.v1
import wget
#from google.api_core.client_options import ClientOptions
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import requests
import mimetypes
import io
from urllib.request import Request, urlopen
import json

from io import StringIO
st.set_page_config(layout="wide")


st.header("Sir Brian's app")

data = st.experimental_get_query_params()


#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = auth
PROJECT_ID = "oracle-329410"
LOCATION = "us"  # Format is 'us' or 'eu'
PROCESSOR_ID = "382fd7b8bf68f41a"  # Create processor in Cloud Console
PDF_PATH = data["url"][0]


def show_pdf(file_path):
    response = urlopen(file_path)
    f = BytesIO(response.read())
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.write("##")
    # st.dataframe(doc)
    st.write("##")


def edit_df(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    string_to_add_row = "\n\n function(e) { \n \
    let api = e.api; \n \
    let rowIndex = e.rowIndex + 1; \n \
    api.applyTransaction({addIndex: rowIndex, add: [{}]}); \n \
        }; \n \n"

    string_to_delete = "\n\n function(e) { \n \
    let api = e.api; \n \
    let sel = api.getSelectedRows(); \n \
    api.applyTransaction({remove: sel}); \n \
    api.refreshView(); \n \
        }; \n \n"

    cell_button_delete = JsCode('''
    class BtnCellRenderer {
        init(params) {
            console.log(params.api.getSelectedRows());
            this.params = params;
            this.eGui = document.createElement('div');
            this.eGui.innerHTML = `
             <span>
                <style>
                .btn {
                  background-color: #F94721;
                  border: none;
                  color: white;
                  font-size: 10px;
                  font-weight: bold;
                  height: 2.5em;
                  width: 8em;
                  cursor: pointer;
                }

                .btn:hover {
                  background-color: #FB6747;
                }
                </style>
                <button id='click-button'
                    class="btn"
                    >&#128465; Delete</button>
             </span>
          `;
        }

        getGui() {
            return this.eGui;
        }

    };
    ''')

    cell_button_add = JsCode('''
        class BtnAddCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                <span>
                    <style>
                    .btn_add {
                    background-color: limegreen;
                    border: none;
                    color: white;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 10px;
                    font-weight: bold;
                    height: 2.5em;
                    width: 8em;
                    cursor: pointer;
                    }

                    .btn_add :hover {
                    background-color: #05d588;
                    }
                    </style>
                    <button id='click-button' 
                        class="btn_add" 
                        >&CirclePlus; Add</button>
                </span>
            `;
            }

            getGui() {
                return this.eGui;
            }

        };
        ''')

    gb.configure_column('', headerTooltip='Click on Button to add new row', editable=False, filter=False,
                        onCellClicked=JsCode(string_to_add_row), cellRenderer=cell_button_add)

    gb.configure_column('Delete', headerTooltip='Click on Button to remove row',
                        editable=False, filter=False, onCellClicked=JsCode(string_to_delete),
                        cellRenderer=cell_button_delete, checkboxSelection=True)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()
    grid_return = AgGrid(df, editable=True, update_mode=GridUpdateMode.MANUAL,
                         allow_unsafe_jscode=True, gridOptions=grid_options, fit_columns_on_grid_load=True)
    new_df = pd.DataFrame(grid_return['data'])
    return new_df


def process_document_sample():
    # Instantiates a client
    client_options = {
        "api_endpoint": "{}-documentai.googleapis.com".format(LOCATION)}
    client = documentai.DocumentProcessorServiceClient(
        client_options=client_options)

    # The full resource name of the processor, e.g.:
    # projects/project-id/locations/location/processor/processor-id
    # You must create new processors in the Cloud Console first
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

    # with open(PDF_PATH, "rb") as image:
    #    image_content = image.read()

    # Load PDF via URL directly
    response = requests.get(PDF_PATH)
    image_content = response.content

    # Auto detect MIME TYPE of files
    mime_type = mimetypes.guess_type(PDF_PATH)[0]

    # Read the file into memory
    document = {"content": image_content, "mime_type": mime_type}

    # Configure the process request
    request = {"name": name, "raw_document": document}

    # Recognizes text entities in the PDF document
    result = client.process_document(request=request)
    document = result.document
    entities = document.entities
    print("Document processing complete.\n\n")

    # For a full list of Document object attributes, please reference this page: https://googleapis.dev/python/documentai/latest/_modules/google/cloud/documentai_v1beta3/types/document.html#Document
    types = []
    values = []
    confidence = []

    # Grab each key/value pair and their corresponding confidence scores.
    for entity in entities:
        types.append(entity.type_)
        values.append(entity.mention_text)
        confidence.append(round(entity.confidence, 4))

    # Create a Pandas Dataframe to print the values in tabular format.
    df = pd.DataFrame({'Type': types, 'Value': values})

    # if result.human_review_operation:
    #    print ("Triggered HITL long running operation: {}".format(result.human_review_operation))

    return df


show_pdf(PDF_PATH)

# --- Initialising SessionState ---
if "load_state" not in st.session_state:
    st.session_state.load_state = False


if st.button('Process OCR') or st.session_state.load_state:
    st.session_state.load_state = True
    doc = process_document_sample()
else:
    st.write('Click to process OCR')

try:
    test_df = edit_df(doc)
except Exception:
    pass

if st.button('Mark Invalid'):
    print('Entry marked as invalid doc in DB')
else:
    st.write('Mark document as invalid')


if st.button('Push to DB'):
    st.dataframe(test_df)
else:
    st.write('Submit when done')
