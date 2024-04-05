import base64
import io
import subprocess

from openai import OpenAI
from pdf2image import convert_from_path


def get_openai_token():
    return (
        subprocess.check_output(
            "op item get ygji4imam6yd4w46xvwxjju7yi --fields neobea-token", shell=True
        )
        .decode()
        .strip()
    )


client = OpenAI(api_key=get_openai_token())

# Path to your image
image_path = "example.pdf"


def encode_image(image_path):
    # Convert the first page of the PDF to an image
    images = convert_from_path(image_path)
    image = images[0]

    # Save the image to a bytes buffer
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")

    # Get the base64 representation
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# Getting the base64 string

prompt = """
You are an AI assistant that accurately extracts information from documents and responds with structured data in JSON format. If you can't find any information, just leave the key with an empty value.
This is a picture of an invoice, contract, receipt, travel document, or other document. 
In case of invoices an invoice can be outgoing or incoming. one of the entities on the invoice must be the following:
- KATIKO Kft
- NordQuant GmbH
- Toth Zoltan Csaba 

Don't use accents in company names

Most of these documents will be either in German, Hungarian or English

If both KATIKO KFt and Toth Zoltan Csaba is present on the invoice, it's an invoice for KATIKO Kft
If both NordQuant GmBH and Toth Zoltan Csaba is present on the invoice, it's an invoice for NordQuant GmBH

Please extract the following information from the document and reply in a json dictioary using the next key-value format:
key: document_type, value: [invoice, contract, receipt, travel document, other]
in case of an incoice:
   is it an incoming or outgoing invoice? (key: invoice_type, value: [incoming, outgoing])
    the name of the company (key: company_name, value: [KATIKO Kft, NordQuant GmBH, Toth Zoltan Csaba])
    the other party's name (key: other_party_name, value: The other party's name and address)
    the date of the invoice (key: date, value: The date of the invoice). The date format is YYYY-MM-DD
    The completion date of the invoice (key: completion_date, value: The completion date of the invoice). The date format is YYYY-MM-DD 
    The items on the invoice (key: items, value: The items on the invoice)
    The total amount on the invoice (key: total_amount, value: The total amount on the invoice)

In case of a receipt, please extract all the information you can find on the receipt from those that are listed above for the invoices.
In case of a contract, please extract all the information you can find on the contract from those that are listed above for the invoices. Also add a one-sentence summary of the contract (key: summary, value: The one-sentence summary of the contract)

Only extract the information that is present on the document and only reply with a syntactically correct json dictionary. If there are keys you can't find, just leave them in with an empty value.
"""


def extract_data(image_path):
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    return response.choices[0].message.content.strip("```json\n").strip("```")


# %%
