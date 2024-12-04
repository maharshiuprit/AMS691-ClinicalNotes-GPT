from flask import Flask, request, jsonify, send_file
from docx import Document
import requests
import openai
import anthropic
import os
import json
import tempfile
import google.generativeai as genai
import assemblyai as aai

app = Flask(__name__)

# Paths for the Word template and output file
TEMPLATE_PATH = "report.docx"  # Template file path
OUTPUT_PATH = os.path.join(os.getcwd(), "tmp", "populated_report.docx")
ASSEMBLYAI_API_KEY=os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")


# ChatGPT integration
# def process_with_chatgpt(transcribed_text):
#     client = openai.OpenAI()
#     try:
#         print("inside gpt")
#         # Define the prompt
#         prompt = (
#             "The following text is a transcription of a meeting. Extract key information "
#             "and return it in the form of pre-defined key-value pairs (JSON format). Keys should include 'doctor', "
#             "'Date', 'specialization', 'patient', 'DateBd', 'medNumber', 'ihi', 'patientPhone', 'email', "
#             "'assessment', 'diagnosis', and 'prescription':\n\n"
#             f"{transcribed_text}"
#         )

#         # Call the ChatCompletion API for GPT-4
#         response = client.chat.completions.create(
#             model="gpt-4",  # Use GPT-4
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#         )

#         # Extract the assistant's message content
#         return response.choices[0].message.content

#     except Exception as e:
#         raise RuntimeError(f"Error processing text with ChatGPT: {str(e)}")

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
                {"role": "user", "content":prompt }
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


@app.route('/process-audio', methods=['POST'])
def process_audio():
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        audio_file = request.files['audio_file']
        audio_file.save('temp_audio_file.mp3')

        audio_file = (
                "./temp_audio_file.mp3"
            )

        config = aai.TranscriptionConfig(
            speaker_labels=True,
        )

        transcript = aai.Transcriber().transcribe(audio_file, config)

        transcribed_text=""

        for utterance in transcript.utterances:
            transcribed_text += utterance.speaker+":"+utterance.text

        print(transcribed_text)

        # Step 4: Use ChatGPT to extract key-value pairs
        key_value_pairs = process_with_gemini(transcribed_text)

        populate_docx(TEMPLATE_PATH, OUTPUT_PATH, key_value_pairs)
        print(f"Document saved at {OUTPUT_PATH}")
        # Comment out the send_file line for now
        # return send_file(OUTPUT_PATH, as_attachment=True)
        return jsonify({"message": f"File saved at {OUTPUT_PATH}"})


    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists('temp_audio_file.mp3'):
            os.remove('temp_audio_file.mp3')

if __name__ == '__main__':
    app.run(debug=True)
