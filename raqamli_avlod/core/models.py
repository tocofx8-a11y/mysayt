from django.conf import settings
from django.db import models


class Course(models.Model):
    """
    Kurs — masalan "Ingliz tili", "Matematika", "Dasturlash".
    Faqat Super Admin yarata oladi.
    """
    name = models.CharField(max_length=150, verbose_name='Kurs nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_courses',
        limit_choices_to={'role': 'super_admin'},
        verbose_name='Kimtomonidan yaratilgan',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    Guruh — masalan "G41", "H45". Har bir guruh bitta kursga
    va bitta o'qituvchiga bog'langan bo'ladi. Guruhni Super Admin yaratadi
    va o'qituvchini biriktiradi.
    """
    name = models.CharField(max_length=50, verbose_name='Guruh nomi')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='groups', verbose_name='Kurs'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_groups',
        limit_choices_to={'role': 'teacher'},
        verbose_name="Biriktirilgan o'qituvchi",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        limit_choices_to={'role': 'super_admin'},
        verbose_name='Kim tomonidan yaratilgan',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        unique_together = ('name', 'course')

    def __str__(self):
        return f'{self.name} ({self.course.name})'


class ControlExam(models.Model):
    """
    Nazorat ishi — haftalik yoki oylik yakun bo'yicha guruh uchun
    Admin tomonidan joylanadigan imtihon.
    """
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='control_exams', verbose_name='Guruh'
    )
    title = models.CharField(max_length=200, verbose_name='Nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif / savollar matni')
    attachment = models.FileField(
        upload_to='control_exams/', blank=True, null=True, verbose_name='Fayl (ixtiyoriy)'
    )
    max_score = models.PositiveIntegerField(default=100, verbose_name="Maksimal ball")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exams',
        limit_choices_to={'role': 'admin'},
        verbose_name='Kim joylagan',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Nazorat ishi'
        verbose_name_plural = 'Nazorat ishlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.group.name}'


class ControlExamScore(models.Model):
    """
    Har bir talabaning muayyan nazorat ishidan olgan bahosi.
    Admin tomonidan tekshirilib, ball qo'yiladi.
    """
    exam = models.ForeignKey(ControlExam, on_delete=models.CASCADE, related_name='scores', verbose_name='Nazorat ishi')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='control_exam_scores',
        limit_choices_to={'role': 'student'},
        verbose_name='Talaba',
    )
    answer_file = models.FileField(
        upload_to='control_exam_answers/', blank=True, null=True, verbose_name='Talaba javobi (fayl)'
    )
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ball')
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_exam_scores',
        verbose_name='Kim baholadi',
    )
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name='Baholangan vaqt')

    # --- AI (Gemini) taklifi: talaba javob yuklagach avtomatik to'ldiriladi,
    # lekin yakuniy ballni faqat Admin qo'yadi (score maydoni) ---
    ai_score = models.PositiveIntegerField(null=True, blank=True, verbose_name='AI taklif qilgan ball')
    ai_feedback = models.TextField(blank=True, verbose_name='AI izohi')
    ai_checked_at = models.DateTimeField(null=True, blank=True, verbose_name='AI tekshirgan vaqt')

    class Meta:
        verbose_name = 'Nazorat ishi bahosi'
        verbose_name_plural = 'Nazorat ishi baholari'
        unique_together = ('exam', 'student')

    def __str__(self):
        return f'{self.student} — {self.exam}: {self.score if self.score is not None else "baholanmagan"}'
class GroupMembership(models.Model):
    """
    Talabaning muayyan guruhga a'zoligi. Talabani guruhga biriktirish
    va guruhdan chiqarish — Admin vazifasi.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        limit_choices_to={'role': 'student'},
        verbose_name='Talaba',
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='memberships', verbose_name='Guruh'
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_memberships',
        verbose_name='Kim biriktirgan (Admin)',
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='Guruhda faolmi')
    removed_at = models.DateTimeField(null=True, blank=True, verbose_name='Guruhdan chiqarilgan vaqt')

    class Meta:
        verbose_name = "Guruh a'zoligi"
        verbose_name_plural = "Guruh a'zoliklari"
        unique_together = ('student', 'group')

    def __str__(self):
        holat = 'faol' if self.is_active else 'chiqarilgan'
        return f'{self.student} — {self.group} ({holat})'


# ============================================================
#  DARSLAR VA UYGA VAZIFA TIZIMI (O'qituvchi paneli uchun)
# ============================================================

class Lesson(models.Model):
    """
    Dars — o'qituvchi tomonidan muayyan guruh uchun qo'shiladi,
    maruza matni bilan birga keladi. Har bir darsning bitta
    Uyga vazifa (Homework) bo'limi bo'ladi.

    Agar dars Open Access kursi uchun bo'lsa, `group` bo'sh qoladi va
    `course` to'g'ridan-to'g'ri bog'lanadi (guruhsiz, ochiq kirish).
    """
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='lessons', null=True, blank=True, verbose_name='Guruh',
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='open_lessons', null=True, blank=True,
        verbose_name='Kurs (Open Access uchun)',
    )
    title = models.CharField(max_length=200, verbose_name='Dars mavzusi')
    lecture_text = models.TextField(blank=True, verbose_name='Maruza matni')
    lecture_file = models.FileField(
        upload_to='lecture_files/', null=True, blank=True,
        verbose_name='Maruza fayli (ixtiyoriy)',
        help_text='PDF, Word, PowerPoint yoki boshqa fayl — matn o\'rniga yoki qo\'shimcha sifatida yuklashingiz mumkin.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lessons',
        verbose_name="Kim qo'shgan",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib raqami')

    class Meta:
        verbose_name = 'Dars'
        verbose_name_plural = 'Darslar'
        ordering = ['order', 'created_at']

    @property
    def is_open_access(self):
        return self.group_id is None

    def __str__(self):
        if self.group_id:
            return f'{self.title} ({self.group.name})'
        course_name = self.course.name if self.course_id else 'Open Access'
        return f'{self.title} (Open Access — {course_name})'


class Homework(models.Model):
    """
    Har bir darsning uyga vazifa bo'limi. 4 qismdan iborat:
    1) Video dars  2) Topshiriq (3 daraja)  3) Savol-javob  4) Quiz/test
    Umumiy ball taqsimoti: 5 + 60(10+20+30) + 10 + 15 = 100,
    + darsda faollik uchun alohida 10 ball.
    """
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='homework', verbose_name='Dars')
    created_at = models.DateTimeField(auto_now_add=True)

    VIDEO_SCORE = 5
    TASK_TOTAL_SCORE = 60
    QUESTIONS_SCORE = 10
    QUIZ_SCORE = 15
    ACTIVITY_SCORE = 10

    class Meta:
        verbose_name = 'Uyga vazifa'
        verbose_name_plural = 'Uyga vazifalar'

    def __str__(self):
        return f"Uyga vazifa — {self.lesson.title}"


class HomeworkVideo(models.Model):
    """1-qism: Video dars. Talaba oxirigacha ko'rmaguncha keyingi qism ochilmaydi."""
    homework = models.OneToOneField(Homework, on_delete=models.CASCADE, related_name='video_part', verbose_name='Uyga vazifa')
    video_url = models.URLField(blank=True, verbose_name='Video havolasi (YouTube va h.k.)')
    video_file = models.FileField(upload_to='lesson_videos/', blank=True, null=True, verbose_name='Video fayl (ixtiyoriy)')

    class Meta:
        verbose_name = 'Video dars'
        verbose_name_plural = 'Video darslar'

    def __str__(self):
        return f'Video — {self.homework.lesson.title}'


class TaskLevel(models.Model):
    """
    2-qism: Topshiriq, 3 darajali (oson/o'rtacha/qiyin).
    Har bir darajaga kirish uchun kod so'raladi (dars davomida aytiladi).
    Ball: oson=10, o'rtacha=20, qiyin=30 (jami 60).
    """
    class Level(models.TextChoices):
        EASY = 'easy', 'Oson'
        MEDIUM = 'medium', "O'rtacha"
        HARD = 'hard', 'Qiyin'

    LEVEL_SCORES = {
        Level.EASY: 10,
        Level.MEDIUM: 20,
        Level.HARD: 30,
    }

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='task_levels', verbose_name='Uyga vazifa')
    level = models.CharField(max_length=10, choices=Level.choices, verbose_name='Daraja')
    instructions = models.TextField(verbose_name='Topshiriq matni')
    access_code = models.CharField(max_length=50, verbose_name='Kirish kodi')

    class Meta:
        verbose_name = 'Topshiriq darajasi'
        verbose_name_plural = 'Topshiriq darajalari'
        unique_together = ('homework', 'level')
        ordering = ['level']

    @property
    def max_score(self):
        return self.LEVEL_SCORES.get(self.level, 0)

    def __str__(self):
        return f'{self.get_level_display()} — {self.homework.lesson.title}'


class HomeworkQuestion(models.Model):
    """3-qism: Savollar bo'limi. O'qituvchi savol beradi, talaba javob yozadi."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='questions', verbose_name='Uyga vazifa')
    text = models.TextField(verbose_name='Savol matni')
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib raqami')

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class QuizQuestion(models.Model):
    """4-qism: Quiz/test bo'limi — 4 variantli savollar."""
    class Option(models.TextChoices):
        A = 'A', 'A'
        B = 'B', 'B'
        C = 'C', 'C'
        D = 'D', 'D'

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='quiz_questions', verbose_name='Uyga vazifa')
    text = models.TextField(verbose_name='Savol matni')
    option_a = models.CharField(max_length=255, verbose_name='A variant')
    option_b = models.CharField(max_length=255, verbose_name='B variant')
    option_c = models.CharField(max_length=255, verbose_name='C variant')
    option_d = models.CharField(max_length=255, verbose_name='D variant')
    correct_option = models.CharField(max_length=1, choices=Option.choices, verbose_name="To'g'ri javob")
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib raqami')

    class Meta:
        verbose_name = 'Quiz savoli'
        verbose_name_plural = 'Quiz savollari'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


# ============================================================
#  TALABA PROGRESSI VA BAHOLAR (Talaba paneli uchun)
# ============================================================

class VideoProgress(models.Model):
    """1-qism: talaba videoni oxirigacha ko'rganini belgilaydi (avtomatik 5 ball)."""
    video_part = models.ForeignKey(HomeworkVideo, on_delete=models.CASCADE, related_name='progress', verbose_name='Video')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progress',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Video ko\'rish belgisi'
        verbose_name_plural = 'Video ko\'rish belgilari'
        unique_together = ('video_part', 'student')

    def __str__(self):
        return f'{self.student} — {self.video_part} ko\'rdi'


class TaskSubmission(models.Model):
    """2-qism: talaba kirish kodini kiritib topshiriqni ochadi va javob faylini yuklaydi."""
    task_level = models.ForeignKey(TaskLevel, on_delete=models.CASCADE, related_name='submissions', verbose_name='Daraja')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_submissions',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    unlocked_at = models.DateTimeField(null=True, blank=True, verbose_name='Kod bilan ochilgan vaqt')
    answer_file = models.FileField(upload_to='task_answers/', blank=True, null=True, verbose_name='Javob fayli')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Yuklangan vaqt')
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ball')
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='graded_task_submissions', verbose_name='Kim baholadi',
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    # --- AI (Gemini) taklifi: talaba javob yuklagach avtomatik to'ldiriladi,
    # lekin yakuniy ballni faqat O'qituvchi qo'yadi (score maydoni) ---
    ai_score = models.PositiveIntegerField(null=True, blank=True, verbose_name='AI taklif qilgan ball')
    ai_feedback = models.TextField(blank=True, verbose_name='AI izohi')
    ai_checked_at = models.DateTimeField(null=True, blank=True, verbose_name='AI tekshirgan vaqt')

    class Meta:
        verbose_name = 'Topshiriq javobi'
        verbose_name_plural = 'Topshiriq javoblari'
        unique_together = ('task_level', 'student')

    @property
    def is_unlocked(self):
        return self.unlocked_at is not None

    def __str__(self):
        return f'{self.student} — {self.task_level}'


class QuestionAnswer(models.Model):
    """3-qism: talabaning savolga yozgan javobi."""
    question = models.ForeignKey(HomeworkQuestion, on_delete=models.CASCADE, related_name='answers', verbose_name='Savol')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_answers',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    answer_text = models.TextField(verbose_name='Javob matni')
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Savolga javob'
        verbose_name_plural = 'Savollarga javoblar'
        unique_together = ('question', 'student')

    def __str__(self):
        return f'{self.student} — {self.question}'


class QuizResult(models.Model):
    """4-qism: talabaning quiz natijasi — avtomatik hisoblanadi (15 balldan)."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='quiz_results', verbose_name='Uyga vazifa')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_results',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    correct_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0, verbose_name='Ball (15 balldan)')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz natijasi'
        verbose_name_plural = 'Quiz natijalari'
        unique_together = ('homework', 'student')

    def __str__(self):
        return f'{self.student} — {self.homework}: {self.correct_count}/{self.total_count}'


class QuizAnswer(models.Model):
    """Talabaning har bir quiz savoliga bergan javobi (audit uchun)."""
    quiz_question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='student_answers')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_answers',
        limit_choices_to={'role': 'student'},
    )
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('quiz_question', 'student')

    def __str__(self):
        return f'{self.student} — {self.quiz_question}: {self.selected_option}'


class HomeworkGrade(models.Model):
    """
    3-qism (savol-javob) va Faollik uchun umumiy ball — o'qituvchi tomonidan qo'yiladi.
    Har bir (uyga vazifa, talaba) juftligi uchun bitta yozuv.
    """
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='grades', verbose_name='Uyga vazifa')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='homework_grades',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    questions_score = models.PositiveIntegerField(null=True, blank=True, verbose_name='3-qism ball (0-10)')
    activity_score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Faollik ball (0-10)')
    ai_feedback = models.TextField(blank=True, verbose_name='AI izohi (Open Access uchun)')
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='graded_homework_grades', verbose_name='Kim baholadi',
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Uyga vazifa bahosi'
        verbose_name_plural = 'Uyga vazifa baholari'
        unique_together = ('homework', 'student')

    def __str__(self):
        return f'{self.student} — {self.homework}'


class Certificate(models.Model):
    """Kursni yakunlagan talabaga Admin tomonidan beriladigan sertifikat."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='certificates', verbose_name='Guruh')
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='issued_certificates', limit_choices_to={'role': 'admin'}, verbose_name='Kim berdi',
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sertifikat'
        verbose_name_plural = 'Sertifikatlar'
        unique_together = ('student', 'group')

    def __str__(self):
        return f'{self.student} — {self.group} sertifikati'


# ============================================================
#  KUZATUV PANELI (Kuzatuvchi tomonidan tanishib chiqish belgisi)
# ============================================================

class ObserverConfirmation(models.Model):
    """
    Kuzatuvchi talabaning baholari bilan tanishib, "Tanishib chiqdim" tugmasini
    bosganda shu yerga (yoki yangilanadi). Admin Monitoring bo'limida
    kim tanishib chiqqani, qachon tanishgani ko'rinadi.
    """
    observer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='confirmations_made',
        limit_choices_to={'role': 'observer'}, verbose_name='Kuzatuvchi',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='observer_confirmations',
        limit_choices_to={'role': 'student'}, verbose_name='Talaba',
    )
    confirmed_at = models.DateTimeField(auto_now=True, verbose_name='Tanishib chiqqan vaqti')

    class Meta:
        verbose_name = 'Tanishib chiqish belgisi'
        verbose_name_plural = 'Tanishib chiqish belgilari'
        unique_together = ('observer', 'student')

    def __str__(self):
        return f'{self.observer} — {self.student} bilan tanishdi'


# ============================================================
#  BOSH SAHIFA — KO'RSATMA (mehmon sahifasidagi 2 ta ma'lumot tugmasi)
# ============================================================

class ShowcaseCard(models.Model):
    """
    Kirish (mehmon) sahifasining o'ng tomonida chiqadigan to'rtta tugma.
    Super Admin "Ko'rsatma" bo'limi orqali shu tugmalarning nomi va
    ichidagi matnini boshqaradi. Tugma bosilganda matn oynacha (modal)
    ko'rinishida ochiladi.
    """
    class Slot(models.TextChoices):
        FIRST = 'first', '1-tugma'
        SECOND = 'second', '2-tugma'
        THIRD = 'third', '3-tugma'
        FOURTH = 'fourth', '4-tugma'

    slot = models.CharField(
        max_length=10, choices=Slot.choices, unique=True, verbose_name="O'rni",
    )
    button_label = models.CharField(
        max_length=40, default='Batafsil', verbose_name='Tugma matni',
    )
    title = models.CharField(max_length=150, blank=True, verbose_name='Sarlavha')
    content = models.TextField(blank=True, verbose_name='Matn')
    word_file = models.FileField(
        upload_to='showcase_docs/', null=True, blank=True,
        verbose_name='Word fayldan matn olish (ixtiyoriy)',
        help_text="Word (.docx) fayl yuklasangiz, undagi matn avtomatik ajratib olinib, "
                  "yuqoridagi 'Matn' maydoniga (saytning o'z rangida) joylanadi.",
    )
    content_html = models.TextField(
        blank=True, verbose_name="Word fayldan olingan HTML (rasmlar bilan)",
        help_text="Word fayl yuklanganda avtomatik to'ldiriladi — matn, sarlavha va rasmlarni "
                  "o'z joyida saqlaydi, faqat sayt ranglarida ko'rsatiladi.",
    )
    icon_image = models.ImageField(
        upload_to='showcase_icons/', null=True, blank=True,
        verbose_name='Tugma rasmi (ixtiyoriy)',
        help_text="Yuklansa, tugmada standart belgi o'rniga shu rasm ko'rinadi.",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_showcase_cards',
        verbose_name='Kim tomonidan yangilangan',
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti')

    class Meta:
        verbose_name = "Ko'rsatma tugmasi"
        verbose_name_plural = "Ko'rsatma tugmalari"
        ordering = ('slot',)

    def __str__(self):
        return self.button_label or self.get_slot_display()


# ============================================================
#  OPEN ACCESS (ochiq ro'yxatdan o'tish tizimi)
# ============================================================

class OpenAccessProfile(models.Model):
    """
    Kirish sahifasidan o'zi ro'yxatdan o'tgan (Open Access) foydalanuvchining
    biriktirilgan kursi. Bir foydalanuvchi bitta kursga yoziladi.
    Bu foydalanuvchilarning uyga vazifalarini o'qituvchi emas, AI to'liq
    avtomatik baholaydi.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='open_access_profile',
        limit_choices_to={'role': 'open_access'},
        verbose_name='Foydalanuvchi',
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='open_access_students', verbose_name='Kurs',
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Open Access profili'
        verbose_name_plural = 'Open Access profillari'

    def __str__(self):
        return f'{self.user} — {self.course}'
