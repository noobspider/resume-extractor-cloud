# Resume Extractor — Production

This project extracts structured data from bulk resumes (PDF, DOCX, TXT, images) and exports to Excel.
It uses Flask (web), Celery (worker), Redis (queue), Tesseract + Poppler for OCR, PyMuPDF for PDF text,
and OpenAI for structured parsing.

Quick start (Render cloud):
1. Push this repo to GitHub.
2. Deploy to Render using the included `render.yaml`.
3. Add `OPENAI_API_KEY` to both web & worker environment variables.
4. Open the public URL and upload resumes.

Local Docker Compose:
1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
2. Run: `docker compose up --build`
3. Open http://localhost:3000