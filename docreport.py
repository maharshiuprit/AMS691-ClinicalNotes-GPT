from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
import requests
import anthropic
import google.generativeai as genai
import os
import json
import tempfile


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths for the Word template and output file
TEMPLATE_PATH = "report.docx"  # Template file path
OUTPUT_PATH = os.path.join(os.getcwd(), "tmp", "populated_report.docx")
def process_with_gemini(transcribed_text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")
    try:
        response = model.generate_content(f"The following text is a transcription of a meeting. Extract key information "
                "and return it in the form of a JSON dictionary. The keys should include:\n"
                " - 'doctor'\n"
                " - 'Date'\n"
                " - 'specialization'\n"
                " - 'patient'\n"
                " - 'DateBd'\n"
                " - 'medNumber'\n"
                " - 'ihi'\n"
                " - 'patientPhone'\n"
                " - 'email'\n"
                " - 'assessment' (nested object with presenting_complaint, location, onset, duration, patient_age, patient_gender)\n"
                " - 'diagnosis'\n"
                " - 'prescription'\n\n"
                f"Here is the transcription:\n\n{transcribed_text}\n\n"
                "Return only the JSON object without any additional text or explanation.\n\n"
                "Please return only the object with braces and not other additional text like json so that i can directly process it using json loads")

        print("Raw Response:", response.text)

        try:
            cleaned_input = response.text.strip("```json").rstrip("```").strip()
            cleaned_input = cleaned_input.replace('```', '')
            # Parse as JSON
            return json.loads(cleaned_input)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    except Exception as e:
        raise RuntimeError(f"Error processing text with Gemini: {str(e)}")
    
# Claude integration
def process_with_claude(transcribed_text):
    client = anthropic.Anthropic()
    try:
        print("Inside Claude processing")

        # Define the prompt
        prompt = (
            f"{anthropic.HUMAN_PROMPT} The following text is a transcription of a meeting. Extract key information "
            "and return it in the form of a JSON dictionary. The keys should include:\n"
            " - 'doctor'\n"
            " - 'Date'\n"
            " - 'specialization'\n"
            " - 'patient'\n"
            " - 'DateBd'\n"
            " - 'medNumber'\n"
            " - 'ihi'\n"
            " - 'patientPhone'\n"
            " - 'email'\n"
            " - 'assessment' (nested object with presenting_complaint, location, onset, duration, patient_age, patient_gender)\n"
            " - 'diagnosis'\n"
            " - 'prescription'\n\n"
            f"Here is the transcription:\n\n{transcribed_text}\n\n"
            "Return only the JSON object without any additional text or explanation.\n\n"
            f"{anthropic.AI_PROMPT}"
        )

        # Call the Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        print("Raw Response:", message)

        # Directly parse the JSON string from the response
        try:
            json_response = json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned by Claude: {str(e)}")

        return json_response

    except Exception as e:
        raise RuntimeError(f"Error processing text with Claude: {str(e)}")


# Function to populate the Word document
def populate_docx(template_path, output_path, data):
    try:
        doc = Document(template_path)
        for paragraph in doc.paragraphs:
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"  # Placeholder format: {{key}}
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, value in data.items():
                        placeholder = f"{{{{{key}}}}}"
                        if placeholder in cell.text:
                            cell.text = cell.text.replace(placeholder, str(value))
        doc.save(output_path)
        print(f"Document saved at {output_path}")
    except Exception as e:
        print(f"Error populating Word document: {str(e)}")
        raise


@app.post("/process-audio")
async def process_audio(audio_file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_file.file.read())
            temp_audio_path = temp_audio.name

        # Step 2: Upload the audio file to AssemblyAI
        headers = {'authorization': ASSEMBLYAI_API_KEY}
        with open(temp_audio_path, 'rb') as f:
            response = requests.post(
                'https://api.assemblyai.com/v2/upload',
                headers=headers,
                files={'file': f}
            )
        response.raise_for_status()
        upload_url = response.json()['upload_url']

        # Step 3: Transcribe the audio file
        transcribe_response = requests.post(
            'https://api.assemblyai.com/v2/transcript',
            headers=headers,
            json={'audio_url': upload_url, 'speaker_labels': True}
        )
        transcribe_response.raise_for_status()
        transcript_id = transcribe_response.json()['id']

        # Poll transcription
        while True:
            transcript_result = requests.get(
                f'https://api.assemblyai.com/v2/transcript/{transcript_id}',
                headers=headers
            )
            transcript_result.raise_for_status()
            result_json = transcript_result.json()
            if result_json['status'] == 'completed':
                transcribed_text = result_json['text']
                break
            elif result_json['status'] == 'failed':
                raise HTTPException(status_code=500, detail="Transcription failed")

        print(transcribed_text)

        # Step 4: Use Claude to extract key-value pairs
        key_value_pairs = process_with_claude(transcribed_text)

        populate_docx(TEMPLATE_PATH, OUTPUT_PATH, key_value_pairs)

        # Return the generated Word document
        return FileResponse(
            OUTPUT_PATH,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="generated_report.docx",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
