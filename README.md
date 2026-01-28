# AI Content Pack Generator (AI Blog Studio)

A Django web app that turns a single topic into a complete **content pack**—a long-form blog post plus SEO copy and social posts—then lets you **save and manage** generated posts in your account.

- **Live demo**: https://ai-content-generator-l5eu.onrender.com

---

## Features

- **Content pack generation (one prompt → many outputs)**
  - SEO title (≤ 60 chars)
  - Meta description (140–160 chars)
  - TL;DR (2–3 sentences)
  - Outline (6–10 bullets)
  - Key takeaways (5–8 bullets)
  - Blog post (900–1400 words)
  - 5 tweets (≤ 280 chars each)
  - LinkedIn post (150–250 words)
- **Structured output** via JSON schema (more reliable parsing)
- **Auth**: Signup, login, logout
- **Saved posts**: view all saved blogs and open blog details
- **Production-ready basics**: Postgres support, Gunicorn, WhiteNoise for static files

---

## Tech Stack

- **Framework**: Django
- **AI**: OpenAI API (chat completions with JSON schema response format)
- **Database**: SQLite (local) / Neon Postgres (production via `DATABASE_URL`)
- **Deployment**: Render (live link above)
- **Static files**: WhiteNoise

---

## Routes (high level)

- `/` – Generate a content pack (requires login)
- `/save-blog` – Save generated pack (POST)
- `/blog-list` – View saved blogs
- `/blog-details/<id>/` – View a saved blog
- `/login`, `/signup`, `/logout`
- `/admin/` – Django admin

---

## Run locally

### Prerequisites
- Python 3.x
- An OpenAI API key

### 1) Clone & install

git clone https://github.com/Upnit-b/AI-Content-Generator
cd AI_Content_Pack_Generator

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt


### 2) Configure environment variables
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=          # only if using a compatible proxy
DATABASE_URL=             # set to use Postgres; otherwise SQLite is used


### 3) Migrate & start
cd src
python manage.py migrate
python manage.py runserver

Open http://127.0.0.1:8000

---

## Project Structure
src/
  manage.py
  AI_Content_Pack_Generator/   # Django project settings/urls
  blog_generator/              # Main app (views, models, urls)
  templates/                   # HTML templates
requirements.txt

---

## 📬 Contact

Built by [@Upnit-b](https://github.com/Upnit-b) — feel free to reach out via GitHub Issues for any suggestions or bugs.

---
