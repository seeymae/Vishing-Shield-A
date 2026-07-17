# Vishing-Shield AI

Vishing-Shield AI is a robust security simulation tool designed to detect potential voice phishing (vishing) attempts. It leverages artificial intelligence to transcribe voice inputs and analyze them for suspicious patterns or sensitive information.

## Features
- **Voice Transcription**: Utilizes the OpenAI Whisper model to convert audio files into accurate text.
- **Fraud Detection**: Analyzes transcribed text using custom algorithms to identify high-risk keywords (such as "password," "code," "credit card," etc.).
- **Simulation Environment**: Built on FastAPI, providing a scalable and efficient backend for testing security scenarios.

## Tech Stack
- **Backend**: FastAPI
- **AI/ML**: OpenAI Whisper
- **Data Processing**: Regex, Python-Multipart
- **Version Control**: Git & GitHub

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/seeymae/Vishing-Shield-A.git](https://github.com/seeymae/Vishing-Shield-A.git)
   cd Vishing-Shield-A
Install the dependencies:

Bash
pip install -r requirements.txt
Run the application:

Bash
uvicorn app.main:app --reload
Usage
You can test the API via the Swagger UI available at http://127.0.0.1:8000/docs once the server is running. You can upload audio files or provide text input to simulate phishing calls and view the risk analysis report.
