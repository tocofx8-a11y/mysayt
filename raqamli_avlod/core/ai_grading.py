"""
AI (Gemini) yordamida uyga vazifa / nazorat ishi javoblarini avtomatik
tekshirib, TAKLIF sifatida ball va izoh chiqarish.

MUHIM: bu yerda AI hech qachon yakuniy ballni bazaga o'zi "score" maydoniga
yozmaydi — faqat ai_score / ai_feedback maydonlariga taklif yozadi.
Yakuniy ballni doim odam (o'qituvchi yoki admin) tasdiqlaydi.

ISHGA TUSHIRISH:
1. https://aistudio.google.com saytida bepul Gemini API kalitini oling
   (kredit karta talab qilinmaydi).
2. Loyihaning ASOSIY papkasida (manage.py bilan bir joyda) `gemini_api_key.txt`
   nomli fayl yarating va ichiga faqat kalitni joylashtiring.
   (Yoki GEMINI_API_KEY muhit o'zgaruvchisini o'rnatishingiz mumkin.)
3. Kerakli paketlarni o'rnating:
       pip install -r requirements.txt
"""
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
_API_KEY_FILE = BASE_DIR / 'gemini_api_key.txt'

GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_URL = (
    f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
)


def _get_api_key():
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if key:
        return key
    if _API_KEY_FILE.exists():
        return _API_KEY_FILE.read_text(encoding='utf-8').strip()
    return ''


def extract_text_from_file(django_file):
    """
    .txt / .pdf / .docx fayldan matnni ajratib oladi.
    Fayl turi tushunarsiz yoki matn topilmasa, bo'sh satr qaytaradi.
    """
    if not django_file:
        return ''

    name = django_file.name.lower()
    try:
        django_file.seek(0)
        raw = django_file.read()
    finally:
        try:
            django_file.seek(0)
        except Exception:
            pass

    if name.endswith('.txt'):
        for enc in ('utf-8', 'cp1251', 'latin-1'):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode('utf-8', errors='ignore')

    if name.endswith('.docx'):
        try:
            import io

            import docx
            doc = docx.Document(io.BytesIO(raw))
            return '\n'.join(p.text for p in doc.paragraphs)
        except Exception:
            logger.exception('DOCX faylni o\'qib bo\'lmadi')
            return ''

    if name.endswith('.pdf'):
        try:
            import io

            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return '\n'.join((page.extract_text() or '') for page in reader.pages)
        except Exception:
            logger.exception('PDF faylni o\'qib bo\'lmadi')
            return ''

    return ''


def _call_gemini(prompt):
    """Gemini API'ga so'rov yuboradi, JSON javobni dict qilib qaytaradi yoki None."""
    api_key = _get_api_key()
    if not api_key:
        logger.warning('GEMINI_API_KEY topilmadi — AI baholash o\'tkazib yuborildi.')
        return None

    import urllib.error
    import urllib.request

    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'temperature': 0.2,
        },
    }
    req = urllib.request.Request(
        f'{GEMINI_URL}?key={api_key}',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        logger.error('Gemini API xatosi: %s — %s', e.code, e.read())
        return None
    except Exception:
        logger.exception('Gemini API bilan bog\'lanishda xato')
        return None

    try:
        text = data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError):
        logger.exception('Gemini javobini o\'qib bo\'lmadi: %s', data)
        return None


def extract_html_from_docx(django_file):
    """
    .docx fayldan HTML ajratib oladi — sarlavha, paragraf, ro'yxat va
    RASMLARNI o'z joyida saqlagan holda (rasmlar base64 sifatida ichiga
    joylanadi, alohida fayl sifatida saqlash shart emas).
    Natija hech qanday rang/shrift kodi olib kelmaydi — sof struktura,
    shuning uchun saytning o'z CSS uslubi bilan ko'rsatish mumkin.
    Docx bo'lmasa yoki xato bo'lsa, bo'sh satr qaytaradi.
    """
    if not django_file:
        return ''
    name = django_file.name.lower()
    if not name.endswith('.docx'):
        return ''
    try:
        import mammoth
        django_file.seek(0)
        result = mammoth.convert_to_html(django_file)
        return result.value
    except Exception:
        logger.exception('Word fayldan HTML ajratib bo\'lmadi')
        return ''
    finally:
        try:
            django_file.seek(0)
        except Exception:
            pass


def grade_submission_with_ai(task_text, student_answer_text, max_score):
    """
    Bitta topshiriq/nazorat ishi javobini AI orqali baholaydi.
    Qaytaradi: (score:int|None, feedback:str)
    """
    if not student_answer_text.strip():
        return None, ''

    prompt = f"""Sen tajribali o'qituvchisan. Quyida topshiriq matni va
o'quvchining unga bergan javobi berilgan. Javobni topshiriq talablariga
mosligini tahlil qil va {max_score} balldan necha ballga loyiqligini aniqla.

TOPSHIRIQ MATNI:
{task_text or '(topshiriq matni berilmagan)'}

O'QUVCHI JAVOBI:
{student_answer_text[:6000]}

Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:
{{"score": <0 dan {max_score} gacha butun son>, "feedback": "<o'zbek tilida, 1-2 gapli qisqa izoh: nima yaxshi bajarilgan, nima yetishmaydi>"}}
"""
    result = _call_gemini(prompt)
    if not result:
        return None, ''

    try:
        score = int(result.get('score'))
        score = max(0, min(score, max_score))
    except (TypeError, ValueError):
        score = None
    feedback = str(result.get('feedback', '')).strip()
    return score, feedback


def grade_task_submission(submission, auto_finalize=False):
    """
    TaskSubmission obyektini AI orqali baholab, ai_score/ai_feedback ni saqlaydi.
    auto_finalize=True bo'lsa (Open Access talabalari uchun), AI natijasi
    to'g'ridan-to'g'ri yakuniy `score` maydoniga ham yoziladi — chunki bu
    foydalanuvchilarni tekshiradigan o'qituvchi yo'q.
    """
    from django.utils import timezone

    if not submission.answer_file:
        return
    task_text = submission.task_level.instructions
    answer_text = extract_text_from_file(submission.answer_file)
    score, feedback = grade_submission_with_ai(task_text, answer_text, submission.task_level.max_score)

    submission.ai_score = score
    submission.ai_feedback = feedback
    submission.ai_checked_at = timezone.now()
    update_fields = ['ai_score', 'ai_feedback', 'ai_checked_at']

    if auto_finalize and score is not None:
        submission.score = score
        submission.graded_at = timezone.now()
        update_fields += ['score', 'graded_at']

    submission.save(update_fields=update_fields)


def grade_homework_questions(homework, student):
    """
    Open Access uchun: 3-qism (Savol-javob) va Faollikni AI orqali
    TO'LIQ avtomatik baholab, HomeworkGrade'ni yakunlaydi (o'qituvchi
    tasdig'isiz — chunki Open Access talabalari uchun nazoratchi yo'q).
    """
    from django.utils import timezone

    from .models import HomeworkGrade, QuestionAnswer

    questions = list(homework.questions.all())
    if not questions:
        return

    answers_map = {
        a.question_id: a.answer_text
        for a in QuestionAnswer.objects.filter(question__homework=homework, student=student)
    }

    parts = []
    answered_count = 0
    for q in questions:
        ans = (answers_map.get(q.id) or '').strip()
        if ans:
            answered_count += 1
        parts.append(f"Savol: {q.text}\nJavob: {ans or '(javob yozilmagan)'}")
    combined = '\n\n'.join(parts)

    score, feedback = grade_submission_with_ai(
        task_text="Quyida bir nechta savol va talabaning har biriga yozgan javobi berilgan. "
                   "Javoblarni umumiy baholang.",
        student_answer_text=combined,
        max_score=homework.QUESTIONS_SCORE,
    )

    # Faollik bali: nechta savolga javob yozgani nisbatida (o'qituvchi yo'qligi
    # sababli oddiy, shaffof mezon — barcha savollarga javob yozsa to'liq ball).
    activity_score = round((answered_count / len(questions)) * homework.ACTIVITY_SCORE)

    grade, _ = HomeworkGrade.objects.get_or_create(homework=homework, student=student)
    grade.questions_score = score if score is not None else 0
    grade.activity_score = activity_score
    grade.ai_feedback = feedback
    grade.graded_at = timezone.now()
    grade.save(update_fields=['questions_score', 'activity_score', 'ai_feedback', 'graded_at'])


def grade_control_exam_score(score_obj):
    """ControlExamScore obyektini AI orqali baholab, ai_score/ai_feedback ni saqlaydi."""
    from django.utils import timezone

    if not score_obj.answer_file:
        return
    task_text = score_obj.exam.description
    answer_text = extract_text_from_file(score_obj.answer_file)
    score, feedback = grade_submission_with_ai(task_text, answer_text, score_obj.exam.max_score)

    score_obj.ai_score = score
    score_obj.ai_feedback = feedback
    score_obj.ai_checked_at = timezone.now()
    score_obj.save(update_fields=['ai_score', 'ai_feedback', 'ai_checked_at'])
