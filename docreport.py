from flask import Flask, request, jsonify, send_file
from docx import Document
import requests
import openai
import anthropic
import os
import json
import tempfile

app = Flask(__name__)

# Paths for the Word template and output file
TEMPLATE_PATH = "report.docx"  # Template file path
OUTPUT_PATH = os.path.join(os.getcwd(), "tmp", "populated_report.docx")


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

        # Step 2: Upload the audio file to AssemblyAI
        headers = {'authorization': ASSEMBLYAI_API_KEY}
        with open('temp_audio_file.mp3', 'rb') as f:
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
                return jsonify({'error': 'Transcription failed'}), 500

        print(transcribed_text)

        # Step 4: Use ChatGPT to extract key-value pairs
        key_value_pairs = process_with_claude(transcribed_text)

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
