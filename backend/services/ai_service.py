import os
import re
import io
import pypdf
import psycopg2
import defusedxml.ElementTree as ET
import zipfile
from groq import Groq, RateLimitError, APIError, BadRequestError
from config import Config
from prompts import build_summary_prompt

DATABASE_URL = Config.DATABASE_URL
GROQ_API_KEY = Config.GROQ_API_KEY
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def clean_summary_text(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|[^>]+\|>', '', text)
    cleaned_lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^(?:The|This)\s+(?:document|file|text|report)[,\s]+[^,\n]*?(?:details|explores|discusses|covers|provides|is about)\s+', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^(?:The|This)\s+(?:document|file|text)\s+(?:details|explores|covers|outlines|presents)\s+', '', line, flags=re.IGNORECASE)
        if line:
            # Capitalize first character of each line while preserving original casing (like CIA, DDoS, AI, DevSecOps)
            line = line[0].upper() + line[1:]
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def extract_text_from_file(file_bytes: bytes, original_name: str) -> str:
    ext = os.path.splitext(original_name)[1].lower()
    text = ""
    try:
        bio = io.BytesIO(file_bytes)
        if ext == '.pdf':
            reader = pypdf.PdfReader(bio)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == '.docx':
            with zipfile.ZipFile(bio) as docx:
                tree = ET.fromstring(docx.read('word/document.xml'))
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text = "\n".join("".join(p.itertext()) for p in tree.iterfind('.//w:p', ns))
        elif ext == '.txt':
            text = file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[Extraction Error] {original_name}: {e}")
    return text.strip()

def sample_massive_document(text: str, target_chars: int = 20000) -> str:
    """When a document exceeds the model token/TPM limit."""
    total = len(text)
    if total <= target_chars:
        return text

    part_size = target_chars // 3
    start_chunk = text[:part_size]
    mid_start = (total // 2) - (part_size // 2)
    middle_chunk = text[mid_start:mid_start + part_size]
    end_chunk = text[-part_size:]

    return (
        f"{start_chunk}\n"
        f"{middle_chunk}\n"
        f"{end_chunk}"
    )

def _generate_summary_call(prompt_text: str) -> str:
    chat_completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": build_summary_prompt(prompt_text)}],
        temperature=0.2,
        max_tokens=600,
        timeout=30.0
    )
    content = chat_completion.choices[0].message.content or ""
    return clean_summary_text(content)

def process_file_ai(file_id: int, file_bytes: bytes, original_name: str, mime_type: str = None):
    doc_text = extract_text_from_file(file_bytes, original_name)
    if not doc_text:
        _update_summary(file_id, f"No extractable text found in this {os.path.splitext(original_name)[1]} file.")
        return

    if not groq_client:
        _update_summary(file_id, "Summary unavailable: GROQ_API_KEY not configured.")
        return

    summary = ""
    # If text is already larger than Groq free tier limit (~5,000 tokens / 20k chars), sample proactively
    if len(doc_text) > 20000:
        doc_text = sample_massive_document(doc_text, target_chars=20000)

    try:
        summary = _generate_summary_call(doc_text)
    except (BadRequestError, APIError) as e:
        err_msg = str(e).lower()
        if "too large" in err_msg or "rate_limit_exceeded" in err_msg or "token" in err_msg or "context_length_exceeded" in err_msg:
            print(f"[AI Processor] Document exceeded rate/token limit ({len(doc_text)} chars). Applying smaller smart sampling.")
            try:
                sampled_text = sample_massive_document(doc_text, target_chars=12000)
                summary = _generate_summary_call(sampled_text)
            except Exception as fallback_err:
                print(f"[Fallback Error] {fallback_err}")
                summary = "Summary generation failed for large document."
        else:
            print(f"[Groq Error] {e}")
            summary = "Summary generation failed. Please try again later."
    except RateLimitError:
        summary = "⚠️ Rate limit reached (429): Groq model limit exceeded. Please try again after 1 minute."
    except Exception as e:
        print(f"[AI Error] {e}")
        summary = "Summary generation failed due to connection error."

    _update_summary(file_id, summary or "Summary generation completed.")

def _update_summary(file_id: int, summary: str):
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require' if 'supabase' in DATABASE_URL.lower() else None)
        with conn.cursor() as cur:
            cur.execute("UPDATE files SET summary = %s WHERE id = %s", (summary, file_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Update Error] File {file_id}: {e}")
