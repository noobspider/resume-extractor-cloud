import os, uuid, re
from celery import Celery
from dotenv import load_dotenv
from extractors import extract_text, detect_emails, detect_phones, llm_extract_structured, build_excel

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery.task(bind=True)
def process_files_task(self, file_paths, output_folder):
    results = []
    total = len(file_paths)
    for i, p in enumerate(file_paths, start=1):
        # update Celery progress
        self.update_state(state="PROGRESS", meta={"current": i, "total": total, "file": p})
        text = extract_text(p)
        structured = llm_extract_structured(text)
        # fallbacks
        if not structured.get("Email"):
            emails = detect_emails(text)
            structured["Email"] = emails[0] if emails else ""
        if not structured.get("Phone"):
            phones = detect_phones(text)
            structured["Phone"] = phones[0] if phones else ""
        # normalize
        if isinstance(structured.get("Skills"), str):
            structured["Skills"] = [s.strip() for s in re.split(r"[;,\\n]+", structured.get("Skills")) if s.strip()]
        if isinstance(structured.get("Education"), str):
            structured["Education"] = [s.strip() for s in re.split(r"[;\\n]+", structured.get("Education")) if s.strip()]
        results.append(structured)
    outname = f"All_Resumes_Data_{uuid.uuid4().hex[:6]}.xlsx"
    outpath = os.path.join(output_folder, outname)
    bio = build_excel(results)
    with open(outpath, "wb") as f:
        f.write(bio.getbuffer())
    return {"output": outpath, "count": len(results)}