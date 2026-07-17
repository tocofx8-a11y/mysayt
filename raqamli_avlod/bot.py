"""
Raqamli Avlod — Telegram bot

Bu bot talaba va kuzatuvchi (ota-ona) foydalanuvchilari uchun ishlaydi:
- Saytdagi login/parol bilan botga kiradi
- Talaba: o'z baholarini va reytingini ko'radi
- Kuzatuvchi: biriktirilgan talabaning baholarini, reytingini ko'radi va
  "Tanishib chiqdim" tugmasini bosadi

ISHGA TUSHIRISH:
1. Terminalda (venv faol holatda) o'rnating:
       pip install -r requirements.txt
2. Telegram'da @BotFather orqali bot yarating va tokenni oling.
3. Loyihaning ASOSIY papkasida (manage.py bilan bir joyda) `bot_token.txt`
   nomli fayl yarating va ichiga faqat tokenni joylashtiring.
   (Yoki TELEGRAM_BOT_TOKEN muhit o'zgaruvchisini o'rnatishingiz mumkin.)
4. Ishga tushiring:
       python bot.py

DIQQAT: Bot va veb-sayt (runserver) bir xil SQLite bazasidan foydalanadi.
Ikkalasini bir vaqtda ishlatish mumkin, lekin juda tez-tez yozish
amallarida "database is locked" xatosi chiqishi mumkin — bu SQLite'ning
tabiiy cheklovi, production'da PostgreSQL'ga o'tish tavsiya etiladi.
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import telebot  # noqa: E402  (django.setup() dan keyin import qilinishi kerak)
from telebot import types  # noqa: E402
from django.contrib.auth import authenticate  # noqa: E402

from accounts.models import User  # noqa: E402
from core.models import ControlExamScore, Group, ObserverConfirmation  # noqa: E402
from core.scoring import compute_homework_score, get_latest_grade_update  # noqa: E402


# ---------- TOKEN OLISH ----------
def _load_token():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token:
        return token.strip()
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_token.txt')
    if os.path.exists(token_path):
        with open(token_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


BOT_TOKEN = _load_token()
if not BOT_TOKEN:
    raise RuntimeError(
        "Bot tokeni topilmadi. Loyiha papkasida 'bot_token.txt' fayl yarating "
        "va ichiga @BotFather bergan tokenni joylashtiring, yoki "
        "TELEGRAM_BOT_TOKEN muhit o'zgaruvchisini o'rnating."
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# Login jarayoni uchun vaqtinchalik xotira (chat_id -> {'step': ..., 'username': ...})
sessions = {}


# ============================================================
#  YORDAMCHI FUNKSIYALAR
# ============================================================

def get_logged_in_user(chat_id):
    """Avval botga kirgan va telegram_chat_id saqlangan foydalanuvchini topadi."""
    return User.objects.filter(telegram_chat_id=str(chat_id)).first()


def get_target_student(user):
    """Talaba uchun — o'zi. Kuzatuvchi uchun — unga biriktirilgan talaba."""
    if user.role == User.Role.STUDENT:
        return user
    if user.role == User.Role.OBSERVER:
        return user.observed_student
    return None


def main_menu_markup(user):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user.role == User.Role.STUDENT:
        markup.add(types.KeyboardButton('📊 Baholarim'), types.KeyboardButton('🏆 Reyting'))
    elif user.role == User.Role.OBSERVER:
        markup.add(types.KeyboardButton('📊 Talaba baholari'), types.KeyboardButton('🏆 Reyting'))
        markup.add(types.KeyboardButton('✅ Tanishib chiqdim'))
    return markup


def get_review_note(user):
    """
    Kuzatuvchi uchun: talabaning baholari so'nggi tasdiqdan keyin
    yangilangan bo'lsa, ogohlantiruvchi matn qaytaradi. Talaba uchun None.
    """
    if user.role != User.Role.OBSERVER or not user.observed_student:
        return None
    student = user.observed_student
    confirmation = ObserverConfirmation.objects.filter(observer=user, student=student).first()
    latest_update = get_latest_grade_update(student)
    if not confirmation:
        return "ℹ️ Siz hali talabaning baholari bilan tanishib chiqmagansiz."
    if latest_update and latest_update > confirmation.confirmed_at:
        return "⚠️ Talabaga yangi baho qo'yilgan — iltimos qayta tanishib chiqing."
    return "✅ Siz eng so'nggi baholar bilan tanishib chiqqansiz."


# ============================================================
#  /start VA /logout BUYRUQLARI
# ============================================================

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user = get_logged_in_user(chat_id)
    if user:
        note = get_review_note(user)
        text = f"Xush kelibsiz, *{user.get_full_name()}*!"
        if note:
            text += f"\n\n{note}"
        bot.send_message(chat_id, text, reply_markup=main_menu_markup(user))
        return
    sessions[chat_id] = {'step': 'username'}
    bot.send_message(chat_id, "👋 *Raqamli Avlod* botiga xush kelibsiz!\n\nSaytdagi login (foydalanuvchi nomi)ingizni yuboring:")


@bot.message_handler(commands=['logout'])
def handle_logout(message):
    chat_id = message.chat.id
    user = get_logged_in_user(chat_id)
    if user:
        user.telegram_chat_id = None
        user.save()
    sessions.pop(chat_id, None)
    bot.send_message(
        chat_id,
        "Tizimdan chiqdingiz. Qayta kirish uchun /start buyrug'ini yuboring.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# ============================================================
#  LOGIN JARAYONI (login -> parol)
# ============================================================

@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get('step') == 'username')
def handle_username_input(message):
    chat_id = message.chat.id
    sessions[chat_id]['username'] = message.text.strip()
    sessions[chat_id]['step'] = 'password'
    bot.send_message(chat_id, "Endi parolingizni yuboring:")


@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get('step') == 'password')
def handle_password_input(message):
    chat_id = message.chat.id
    username = sessions.get(chat_id, {}).get('username', '')
    password = message.text.strip()

    # Xavfsizlik uchun parol yozilgan xabarni chatdan o'chirishga harakat qilamiz
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    user = authenticate(username=username, password=password)
    sessions.pop(chat_id, None)

    if user is None or user.role not in (User.Role.STUDENT, User.Role.OBSERVER):
        bot.send_message(
            chat_id,
            "❌ Login yoki parol noto'g'ri, yoki bu hisob turi bot orqali kira olmaydi "
            "(bot faqat Talaba va Kuzatuvchi uchun ishlaydi).\n\nQayta urinish uchun /start yuboring.",
        )
        return

    user.telegram_chat_id = str(chat_id)
    user.save()
    note = get_review_note(user)
    text = f"✅ Xush kelibsiz, *{user.get_full_name()}*!"
    if note:
        text += f"\n\n{note}"
    bot.send_message(chat_id, text, reply_markup=main_menu_markup(user))


# ============================================================
#  ASOSIY MENYU: TUGMA BOSISHLARI
# ============================================================

@bot.message_handler(func=lambda m: m.text in ('📊 Baholarim', '📊 Talaba baholari'))
def handle_grades(message):
    chat_id = message.chat.id
    user = get_logged_in_user(chat_id)
    if not user:
        bot.send_message(chat_id, "Sessiya tugagan, /start yuboring")
        return

    student = get_target_student(user)
    if not student:
        bot.send_message(chat_id, "Sizga hali talaba biriktirilmagan. Admin bilan bog'laning.")
        return

    memberships = student.group_memberships.filter(is_active=True).select_related('group')
    if not memberships:
        bot.send_message(chat_id, "Hali hech qaysi guruhga biriktirilmagan.")
        return

    for m in memberships:
        lines = [f"📚 *{m.group.name}* ({m.group.course.name})", '']
        lessons = m.group.lessons.all()
        if lessons:
            for lesson in lessons:
                score = compute_homework_score(lesson.homework, student)
                lines.append(f"• {lesson.title}: *{score['total']}/{score['max_total']}*")
        else:
            lines.append("_Hali dars joylanmagan_")

        exams = m.group.control_exams.all()
        if exams:
            lines.append('')
            lines.append("*Nazorat ishlari:*")
            for exam in exams:
                score_obj = ControlExamScore.objects.filter(exam=exam, student=student).first()
                if score_obj and score_obj.score is not None:
                    lines.append(f"• {exam.title}: *{score_obj.score}/{exam.max_score}*")
                else:
                    lines.append(f"• {exam.title}: _baholanmagan_")

        bot.send_message(chat_id, '\n'.join(lines))


@bot.message_handler(func=lambda m: m.text == '🏆 Reyting')
def handle_rating_groups(message):
    chat_id = message.chat.id
    user = get_logged_in_user(chat_id)
    student = get_target_student(user) if user else None
    if not student:
        bot.send_message(chat_id, "Talaba topilmadi")
        return

    memberships = student.group_memberships.filter(is_active=True).select_related('group')
    if not memberships:
        bot.send_message(chat_id, "Hali hech qaysi guruhga biriktirilmagan.")
        return

    # Reyting bo'yicha guruh tanlash — dinamik ro'yxat bo'lgani uchun
    # bu qismda inline tugmalar qulayroq (asosiy menyu esa pastki klaviatura bo'lib qoladi).
    markup = types.InlineKeyboardMarkup()
    for m in memberships:
        markup.add(types.InlineKeyboardButton(m.group.name, callback_data=f'rating_{m.group.id}'))
    bot.send_message(chat_id, "Qaysi guruh reytingini ko'rmoqchisiz?", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == '✅ Tanishib chiqdim')
def handle_confirm(message):
    chat_id = message.chat.id
    user = get_logged_in_user(chat_id)
    if not user or user.role != User.Role.OBSERVER or not user.observed_student:
        bot.send_message(chat_id, "Bu amal faqat kuzatuvchilar uchun")
        return

    ObserverConfirmation.objects.update_or_create(observer=user, student=user.observed_student)
    bot.send_message(chat_id, "✅ Tanishib chiqganingiz qayd etildi. Rahmat!")


@bot.callback_query_handler(func=lambda call: call.data.startswith('rating_'))
def handle_rating(call):
    chat_id = call.message.chat.id
    group_id = int(call.data.split('_')[1])
    user = get_logged_in_user(chat_id)
    student = get_target_student(user) if user else None
    if not student:
        bot.answer_callback_query(call.id, "Xatolik yuz berdi")
        return

    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi")
        return

    members = group.memberships.filter(is_active=True).select_related('student')
    lessons = list(group.lessons.all())
    exams = list(group.control_exams.all())

    rows = []
    for m in members:
        lesson_total = sum(compute_homework_score(l.homework, m.student)['total'] for l in lessons)
        exam_total = 0
        for exam in exams:
            score_obj = ControlExamScore.objects.filter(exam=exam, student=m.student).first()
            exam_total += score_obj.score if (score_obj and score_obj.score is not None) else 0
        rows.append((m.student, lesson_total + exam_total))
    rows.sort(key=lambda r: r[1], reverse=True)

    medals = ['🥇', '🥈', '🥉']
    lines = [f"🏆 *{group.name}* reytingi:", '']
    for i, (s, total) in enumerate(rows):
        prefix = medals[i] if i < 3 else f'{i + 1}.'
        marker = ' ⬅️' if s.id == student.id else ''
        lines.append(f"{prefix} {s.get_full_name()} — *{total}* ball{marker}")

    bot.send_message(chat_id, '\n'.join(lines))
    bot.answer_callback_query(call.id)


if __name__ == '__main__':
    print("Bot ishga tushdi... To'xtatish uchun Ctrl+C bosing.")
    bot.infinity_polling()
