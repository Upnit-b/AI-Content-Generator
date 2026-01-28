from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
import logging
import os

from openai import OpenAI

from .models import BlogPost, User

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """Handle both GET (show form) and POST (generate content pack)."""
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        topic = (request.POST.get('topic') or '').strip()

        if not topic or len(topic) < 10:
            return render(request, 'index.html', {
                'error': 'Please enter a topic or description (at least ~10 characters).',
                'title': title,
                'topic': topic,
            })

        pack, error = generate_content_pack(topic=topic, title=title)
        if error or not pack:
            return render(request, 'index.html', {
                'error': error or 'Failed to generate content pack. Check OPENAI_API_KEY and try again.',
                'title': title,
                'topic': topic,
            })

        # Convert lists to JSON strings for hidden form fields
        pack_json = {
            **pack,
            'tweets_json': json.dumps(pack.get('tweets', [])),
            'outline_json': json.dumps(pack.get('outline', [])),
            'key_takeaways_json': json.dumps(pack.get('key_takeaways', [])),
        }

        return render(request, 'index.html', {
            'pack': pack,
            'pack_json': pack_json,
            'title': title,
            'topic': topic,
        })

    return render(request, 'index.html')


def generate_content_pack(topic: str, title: str = "") -> tuple[dict | None, str | None]:
    """Generate a full "Topic -> Blog + SEO + social pack" in ONE call.

    Uses OpenAI Structured Outputs (JSON Schema) so the response is reliably parseable.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API")
    if not api_key:
        return None, "Missing OPENAI_API_KEY (or OPENAI_API) environment variable."

    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    schema = {
        "name": "content_pack",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "seo_title": {"type": "string"},
                "meta_description": {"type": "string"},
                "tldr": {"type": "string"},
                "outline": {"type": "array", "items": {"type": "string"}},
                "key_takeaways": {"type": "array", "items": {"type": "string"}},
                "blog_post": {"type": "string"},
                "tweets": {"type": "array", "items": {"type": "string"}},
                "linkedin_post": {"type": "string"},
            },
            "required": [
                "seo_title",
                "meta_description",
                "tldr",
                "outline",
                "key_takeaways",
                "blog_post",
                "tweets",
                "linkedin_post",
            ],
        },
        "strict": True,
    }

    # Keep the instructions short and explicit.
    # We ask for concise SEO fields, and a blog post that's not "this video says...".
    system = (
        "You are an expert content marketing assistant. "
        "You turn a short topic or idea into a polished, long-form blog post plus SEO and social content. "
        "Write in a professional, engaging tone suitable for a modern SaaS / tech audience by default."
    )

    user_prompt = (
        "The user will give you a topic (and optionally some extra notes). "
        "You must infer a clear angle and audience, and then create a complete content pack.\n\n"
        "Constraints:\n"
        "- seo_title: <= 60 characters (concise, compelling)\n"
        "- meta_description: 140-160 characters\n"
        "- tldr: 2-3 sentences\n"
        "- outline: 6-10 bullet strings\n"
        "- key_takeaways: 5-8 bullet strings\n"
        "- blog_post: 900-1400 words, clear headings, actionable, professional, evergreen\n"
        "- tweets: 5 items, each <= 280 chars, first can be a thread hook\n"
        "- linkedin_post: 1 post (150-250 words) with a short hook + bullets + closing question\n\n"
        f"Optional title provided by user (use if helpful): {title or '(none)'}\n\n"
        "User topic / notes:\n"
        f"{topic}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_schema", "json_schema": schema},
            temperature=0.6,
            max_tokens=2000,
        )
        raw = (response.choices[0].message.content or "").strip()
        return json.loads(raw), None
    except Exception as exc:
        logger.exception("Failed to generate content pack: %s", exc)
        return None, str(exc)


def blog_list(request):
    # Without login_required, request.user is AnonymousUser and this filter will
    # raise a ValueError. Make it consistent with the rest of the app.
    if not request.user.is_authenticated:
        return redirect("login")
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})


def blog_details(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')


@login_required
def save_blog(request):
    """Save a generated content pack via form POST."""
    if request.method != "POST":
        return redirect('/')

    title = (request.POST.get("title") or "").strip()
    topic = (request.POST.get("topic") or "").strip()

    # Reconstruct pack from form fields
    pack = {
        "blog_post": request.POST.get("blog_post", ""),
        "seo_title": request.POST.get("seo_title", ""),
        "meta_description": request.POST.get("meta_description", ""),
        "tldr": request.POST.get("tldr", ""),
        "tweets": json.loads(request.POST.get("tweets", "[]")),
        "linkedin_post": request.POST.get("linkedin_post", ""),
        "outline": json.loads(request.POST.get("outline", "[]")),
        "key_takeaways": json.loads(request.POST.get("key_takeaways", "[]")),
    }

    if not topic:
        return redirect('/')

    new_post = BlogPost.objects.create(
        user=request.user,
        title=title,
        transcript=topic,
        blog_post=pack["blog_post"],
        seo_title=pack["seo_title"],
        meta_description=pack["meta_description"],
        tldr=pack["tldr"],
        tweets=pack["tweets"],
        linkedin_post=pack["linkedin_post"],
        outline=pack["outline"],
        key_takeaways=pack["key_takeaways"],
    )

    return redirect('blog-details', pk=new_post.id)


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message': error_message})

    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
