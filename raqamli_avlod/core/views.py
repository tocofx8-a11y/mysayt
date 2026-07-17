import threading

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import ActivityLog, User, log_activity
from .ai_grading import grade_control_exam_score, grade_homework_questions, grade_task_submission
from .forms import (
    AccessCodeForm, AddStudentToGroupForm, ControlExamAnswerForm, ControlExamForm, CourseForm,
    GroupForm, HomeworkGradeForm, HomeworkQuestionForm, HomeworkVideoForm, LessonForm,
    QuizQuestionForm, ShowcaseCardForm, TaskAnswerUploadForm, TaskLevelForm,
)
from .scoring import compute_homework_score, get_latest_grade_update
from .models import (
    Certificate, ControlExam, ControlExamScore, Course, Group, GroupMembership, Homework,
    HomeworkGrade, HomeworkQuestion, HomeworkVideo, Lesson, ObserverConfirmation, OpenAccessProfile,
    QuestionAnswer, QuizAnswer, QuizQuestion, QuizResult, ShowcaseCard, TaskLevel, TaskSubmission,
    VideoProgress,
)


@role_required('super_admin')
def superadmin_dashboard(request):
    from django.core.paginator import Paginator

    logs_qs = ActivityLog.objects.select_related('actor').order_by('-created_at')
    paginator = Paginator(logs_qs, 10)
    page_number = request.GET.get('page', 1)
    logs_page = paginator.get_page(page_number)

    context = {
        'courses': Course.objects.all(),
        'groups': Group.objects.select_related('course', 'teacher').all(),
        'logs': logs_page,
        'admins': User.objects.filter(role=User.Role.ADMIN),
        'teachers': User.objects.filter(role=User.Role.TEACHER),
    }
    return render(request, 'core/superadmin_dashboard.html', context)


@role_required('super_admin')
def create_course_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            log_activity(request.user, f'"{course.name}" nomli yangi kurs yaratdi')
            messages.success(request, f'"{course.name}" kursi yaratildi')
            return redirect('superadmin_dashboard')
    else:
        form = CourseForm()
    return render(request, 'core/create_course.html', {'form': form})


@role_required('super_admin')
def edit_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            log_activity(request.user, f'"{course.name}" kursini tahrirladi')
            messages.success(request, f'"{course.name}" kursi yangilandi')
            return redirect('superadmin_dashboard')
    else:
        form = CourseForm(instance=course)
    return render(request, 'core/edit_course.html', {'form': form, 'course': course})


@role_required('super_admin')
def showcase_list_view(request):
    """
    Kirish sahifasidagi to'rtta ma'lumot tugmasini boshqarish bo'limi.
    Agar tugmalar hali bazada bo'lmasa, avtomatik yaratib qo'yiladi.
    """
    cards = {c.slot: c for c in ShowcaseCard.objects.all()}
    for slot, default_label in ShowcaseCard.Slot.choices:
        if slot not in cards:
            cards[slot] = ShowcaseCard.objects.create(slot=slot, button_label=default_label)
    ordered_cards = [cards[slot] for slot, _ in ShowcaseCard.Slot.choices]
    return render(request, 'core/showcase_list.html', {'cards': ordered_cards})


@role_required('super_admin')
def edit_showcase_view(request, card_id):
    card = get_object_or_404(ShowcaseCard, id=card_id)
    if request.method == 'POST':
        form = ShowcaseCardForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            card = form.save(commit=False)
            card.updated_by = request.user
            # Word fayl yangi yuklangan bo'lsa, undagi matn (va rasmlarni)
            # ajratib olib saqlaymiz — "Matn" (zaxira) va "content_html" (rasmli) sifatida.
            if 'word_file' in request.FILES:
                from .ai_grading import extract_html_from_docx, extract_text_from_file
                card.word_file.seek(0)
                extracted = extract_text_from_file(card.word_file).strip()
                if extracted:
                    card.content = extracted
                html = extract_html_from_docx(card.word_file)
                card.content_html = html
            card.save()
            log_activity(request.user, f'"{card.button_label}" ko\'rsatma tugmasini yangiladi')
            messages.success(request, f'"{card.button_label}" tugmasi yangilandi')
            return redirect('showcase_list')
    else:
        form = ShowcaseCardForm(instance=card)
    return render(request, 'core/edit_showcase.html', {'form': form, 'card': card})


@role_required('super_admin')
def create_group_view(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            teacher_info = f" va {group.teacher.get_full_name()} o'qituvchini biriktirdi" if group.teacher else ''
            log_activity(request.user, f'"{group.name}" nomli yangi guruh yaratdi{teacher_info}')
            messages.success(request, f'"{group.name}" guruhi yaratildi')
            return redirect('superadmin_dashboard')
    else:
        form = GroupForm()
    return render(request, 'core/create_group.html', {'form': form})


@role_required('super_admin')
def edit_group_view(request, group_id):
    """Super Admin guruh nomini/kursini o'zgartirishi yoki o'qituvchini almashtirishi uchun."""
    group = get_object_or_404(Group, id=group_id)
    old_teacher = group.teacher
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            updated = form.save()
            if updated.teacher != old_teacher:
                if updated.teacher:
                    log_activity(
                        request.user,
                        f'"{updated.name}" guruhiga {updated.teacher.get_full_name()} ni o\'qituvchi sifatida biriktirdi'
                        + (f' ({old_teacher.get_full_name()} o\'rniga)' if old_teacher else ''),
                    )
                else:
                    log_activity(request.user, f'"{updated.name}" guruhidan o\'qituvchini olib tashladi')
            messages.success(request, f'"{updated.name}" guruhi yangilandi')
            return redirect('superadmin_dashboard')
    else:
        form = GroupForm(instance=group)
    return render(request, 'core/edit_group.html', {'form': form, 'group': group})


@role_required('admin')
def admin_dashboard(request):
    context = {
        'groups': Group.objects.select_related('course').all(),
        'students': User.objects.filter(role=User.Role.STUDENT).order_by('-date_joined')[:30],
        'observers': User.objects.filter(role=User.Role.OBSERVER).select_related('observed_student').order_by('-date_joined')[:30],
    }
    return render(request, 'core/admin_dashboard.html', context)


@role_required('admin')
def group_detail_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    memberships = group.memberships.filter(is_active=True).select_related('student')
    member_ids = memberships.values_list('student_id', flat=True)
    available_students = User.objects.filter(role=User.Role.STUDENT, is_active=True).exclude(id__in=member_ids)
    exams = group.control_exams.all()

    if request.method == 'POST' and 'add_student' in request.POST:
        student_id = request.POST.get('student_id')
        student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
        membership, created = GroupMembership.objects.get_or_create(
            student=student, group=group,
            defaults={'added_by': request.user},
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.removed_at = None
            membership.added_by = request.user
            membership.save()
        log_activity(request.user, f"{student.get_full_name()} ni {group.name} guruhga biriktirdi")
        messages.success(request, f"{student.get_full_name()} {group.name} guruhga qo'shildi")
        return redirect('group_detail', group_id=group.id)

    context = {
        'group': group,
        'memberships': memberships,
        'available_students': available_students,
        'exams': exams,
    }
    return render(request, 'core/group_detail.html', context)


@role_required('admin')
def remove_student_from_group_view(request, group_id, membership_id):
    membership = get_object_or_404(GroupMembership, id=membership_id, group_id=group_id)
    if request.method == 'POST':
        membership.is_active = False
        membership.removed_at = timezone.now()
        membership.save()
        log_activity(
            request.user,
            f"{membership.student.get_full_name()} ni {membership.group.name} guruhdan chiqardi",
        )
        messages.success(request, f"{membership.student.get_full_name()} guruhdan chiqarildi")
    return redirect('group_detail', group_id=group_id)


@role_required('admin')
def create_control_exam_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = ControlExamForm(request.POST, request.FILES)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.group = group
            exam.created_by = request.user
            exam.save()
            log_activity(request.user, f'"{exam.title}" nomli nazorat ishini {group.name} guruhi uchun joyladi')
            messages.success(request, 'Nazorat ishi joylandi')
            return redirect('group_detail', group_id=group.id)
    else:
        form = ControlExamForm()
    return render(request, 'core/create_control_exam.html', {'form': form, 'group': group})


@role_required('admin')
def grade_control_exam_view(request, exam_id):
    exam = get_object_or_404(ControlExam, id=exam_id)
    memberships = exam.group.memberships.filter(is_active=True).select_related('student')

    # Har bir talaba uchun ControlExamScore qatorini tayyorlab qo'yamiz
    score_map = {s.student_id: s for s in exam.scores.all()}
    rows = []
    for m in memberships:
        score_obj = score_map.get(m.student_id)
        rows.append({
            'student': m.student,
            'score': score_obj.score if score_obj else None,
            'answer_file': score_obj.answer_file if (score_obj and score_obj.answer_file) else None,
            'ai_score': score_obj.ai_score if score_obj else None,
            'ai_feedback': score_obj.ai_feedback if score_obj else '',
            'ai_checked_at': score_obj.ai_checked_at if score_obj else None,
        })

    if request.method == 'POST':
        for m in memberships:
            field_name = f'score_{m.student_id}'
            raw_value = request.POST.get(field_name, '').strip()
            if raw_value == '':
                continue
            try:
                value = int(raw_value)
            except ValueError:
                continue
            value = max(0, min(value, exam.max_score))
            obj, _ = ControlExamScore.objects.get_or_create(exam=exam, student=m.student)
            obj.score = value
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
            obj.save()
        log_activity(request.user, f'"{exam.title}" nazorat ishi baholarini kiritdi/yangiladi')
        messages.success(request, 'Baholar saqlandi')
        return redirect('grade_control_exam', exam_id=exam.id)

    context = {'exam': exam, 'rows': rows}
    return render(request, 'core/grade_control_exam.html', context)


@role_required('teacher')
def teacher_dashboard(request):
    groups = Group.objects.filter(teacher=request.user).select_related('course').prefetch_related('lessons')
    context = {'groups': groups}
    return render(request, 'core/teacher_dashboard.html', context)


def _teacher_group_or_404(request, group_id):
    """O'qituvchi faqat o'ziga biriktirilgan guruh bilan ishlashi mumkin."""
    return get_object_or_404(Group, id=group_id, teacher=request.user)


def _teacher_lesson_or_404(request, lesson_id):
    return get_object_or_404(Lesson, id=lesson_id, group__teacher=request.user)


def _manage_lesson_or_404(request, lesson_id):
    """
    Dars mazmunini (video/topshiriq/savol/quiz) tahrirlash huquqini tekshiradi:
    O'qituvchi — faqat o'ziga biriktirilgan guruhdagi darsni;
    Admin/Super Admin — faqat Open Access (guruhsiz) darsni boshqarishi mumkin.
    """
    if request.user.role == 'teacher':
        return get_object_or_404(Lesson, id=lesson_id, group__teacher=request.user)
    if request.user.role in ('admin', 'super_admin'):
        return get_object_or_404(Lesson, id=lesson_id, group__isnull=True)
    from django.http import Http404
    raise Http404("Bu darsni boshqarish huquqingiz yo'q.")


@role_required('teacher')
def create_lesson_view(request, group_id):
    group = _teacher_group_or_404(request, group_id)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.group = group
            lesson.created_by = request.user
            lesson.save()
            homework = Homework.objects.create(lesson=lesson)
            HomeworkVideo.objects.create(homework=homework)
            for level, _ in TaskLevel.Level.choices:
                TaskLevel.objects.create(homework=homework, level=level, instructions='', access_code='')
            log_activity(request.user, f'"{lesson.title}" darsini {group.name} guruhi uchun qo\'shdi')
            messages.success(request, 'Dars qo\'shildi. Endi uyga vazifa qismlarini to\'ldiring.')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonForm()
    return render(request, 'core/create_lesson.html', {'form': form, 'group': group})


@role_required('admin', 'super_admin')
def create_open_lesson_view(request, course_id):
    """Admin/Super Admin Open Access kursi uchun yangi dars qo'shadi (guruhsiz)."""
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.group = None
            lesson.created_by = request.user
            lesson.save()
            homework = Homework.objects.create(lesson=lesson)
            HomeworkVideo.objects.create(homework=homework)
            for level, _ in TaskLevel.Level.choices:
                TaskLevel.objects.create(homework=homework, level=level, instructions='', access_code='')
            log_activity(request.user, f'"{lesson.title}" darsini {course.name} (Open Access) kursi uchun qo\'shdi')
            messages.success(request, 'Dars qo\'shildi. Endi uyga vazifa qismlarini to\'ldiring.')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonForm()
    return render(request, 'core/create_lesson.html', {'form': form, 'course': course, 'group': None})


@role_required('admin', 'super_admin')
def open_access_admin_view(request):
    """Open Access boshqaruvi: kurslar va ro'yxatdan o'tgan foydalanuvchilar ro'yxati."""
    courses = Course.objects.filter(is_active=True)
    profiles = OpenAccessProfile.objects.select_related('user', 'course').order_by('-registered_at')
    return render(request, 'core/open_access_admin.html', {'courses': courses, 'profiles': profiles})


@role_required('admin', 'super_admin')
def open_access_course_lessons_view(request, course_id):
    """Muayyan Open Access kursining darslar ro'yxati (Admin uchun)."""
    course = get_object_or_404(Course, id=course_id)
    lessons = course.open_lessons.all()
    return render(request, 'core/open_access_course_lessons.html', {'course': course, 'lessons': lessons})


@role_required('open_access')
def open_access_dashboard_view(request):
    """Open Access foydalanuvchisining shaxsiy paneli: kursi va darslari."""
    profile = get_object_or_404(OpenAccessProfile, user=request.user)
    course = profile.course
    lessons = list(course.open_lessons.all())
    today_lesson = lessons[-1] if lessons else None
    other_lessons = lessons[:-1] if len(lessons) > 1 else []

    lesson_rows = []
    for lesson in lessons:
        score = compute_homework_score(lesson.homework, request.user)
        lesson_rows.append({'lesson': lesson, 'score': score})

    context = {
        'course': course,
        'today_lesson': today_lesson,
        'other_lessons': other_lessons,
        'lesson_rows': lesson_rows,
    }
    return render(request, 'core/open_access_dashboard.html', context)


@role_required('teacher', 'admin', 'super_admin')
def edit_lesson_view(request, lesson_id):
    """Dars mavzusi, maruza matni, fayli va tartib raqamini tahrirlash."""
    lesson = _manage_lesson_or_404(request, lesson_id)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            log_activity(request.user, f'"{lesson.title}" darsini tahrirladi')
            messages.success(request, 'Dars ma\'lumotlari yangilandi.')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'core/edit_lesson.html', {'form': form, 'lesson': lesson})


@role_required('teacher', 'admin', 'super_admin')
def lesson_detail_view(request, lesson_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    homework = lesson.homework
    context = {
        'lesson': lesson,
        'homework': homework,
        'video_part': getattr(homework, 'video_part', None),
        'task_levels': homework.task_levels.all(),
        'questions': homework.questions.all(),
        'quiz_questions': homework.quiz_questions.all(),
    }
    return render(request, 'core/lesson_detail.html', context)


@role_required('teacher', 'admin', 'super_admin')
def edit_video_view(request, lesson_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    video_part, _ = HomeworkVideo.objects.get_or_create(homework=lesson.homework)
    if request.method == 'POST':
        form = HomeworkVideoForm(request.POST, request.FILES, instance=video_part)
        if form.is_valid():
            form.save()
            log_activity(request.user, f'"{lesson.title}" darsi uchun video (1-qism) joyladi')
            messages.success(request, 'Video saqlandi (1-qism)')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = HomeworkVideoForm(instance=video_part)
    return render(request, 'core/edit_video.html', {'form': form, 'lesson': lesson})


@role_required('teacher', 'admin', 'super_admin')
def edit_task_level_view(request, lesson_id, level):
    lesson = _manage_lesson_or_404(request, lesson_id)
    valid_levels = dict(TaskLevel.Level.choices)
    if level not in valid_levels:
        return redirect('lesson_detail', lesson_id=lesson.id)
    task_level, _ = TaskLevel.objects.get_or_create(homework=lesson.homework, level=level)
    if request.method == 'POST':
        form = TaskLevelForm(request.POST, instance=task_level)
        if form.is_valid():
            form.save()
            log_activity(
                request.user,
                f'"{lesson.title}" darsi uchun {task_level.get_level_display()} topshiriqni (2-qism) joyladi',
            )
            messages.success(request, f'{task_level.get_level_display()} topshiriq saqlandi')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = TaskLevelForm(instance=task_level)
    return render(request, 'core/edit_task_level.html', {'form': form, 'lesson': lesson, 'task_level': task_level})


@role_required('teacher', 'admin', 'super_admin')
def manage_questions_view(request, lesson_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    if request.method == 'POST':
        form = HomeworkQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.homework = lesson.homework
            question.save()
            log_activity(request.user, f'"{lesson.title}" darsi uchun savol (3-qism) qo\'shdi')
            messages.success(request, 'Savol qo\'shildi')
            return redirect('manage_questions', lesson_id=lesson.id)
    else:
        form = HomeworkQuestionForm()
    questions = lesson.homework.questions.all()
    return render(request, 'core/manage_questions.html', {'form': form, 'lesson': lesson, 'questions': questions})


@role_required('teacher', 'admin', 'super_admin')
def delete_question_view(request, lesson_id, question_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    question = get_object_or_404(HomeworkQuestion, id=question_id, homework=lesson.homework)
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Savol o'chirildi")
    return redirect('manage_questions', lesson_id=lesson.id)


@role_required('teacher', 'admin', 'super_admin')
def manage_quiz_view(request, lesson_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            quiz_q = form.save(commit=False)
            quiz_q.homework = lesson.homework
            quiz_q.save()
            log_activity(request.user, f'"{lesson.title}" darsi uchun quiz savoli (4-qism) qo\'shdi')
            messages.success(request, 'Quiz savoli qo\'shildi')
            return redirect('manage_quiz', lesson_id=lesson.id)
    else:
        form = QuizQuestionForm()
    quiz_questions = lesson.homework.quiz_questions.all()
    return render(request, 'core/manage_quiz.html', {'form': form, 'lesson': lesson, 'quiz_questions': quiz_questions})


@role_required('teacher', 'admin', 'super_admin')
def delete_quiz_question_view(request, lesson_id, question_id):
    lesson = _manage_lesson_or_404(request, lesson_id)
    question = get_object_or_404(QuizQuestion, id=question_id, homework=lesson.homework)
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Quiz savoli o'chirildi")
    return redirect('manage_quiz', lesson_id=lesson.id)


@role_required('student')
def student_dashboard(request):
    context = {
        'memberships': request.user.group_memberships.filter(is_active=True).select_related('group', 'group__course'),
    }
    return render(request, 'core/student_dashboard.html', context)


# ============================================================
#  TALABA PANELI
# ============================================================

def _student_membership_or_404(request, group_id):
    return get_object_or_404(GroupMembership, group_id=group_id, student=request.user, is_active=True)


def _student_lesson_or_404(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if lesson.group_id is None:
        # Open Access dars — faqat shu kursga yozilgan Open Access foydalanuvchi kira oladi
        profile = getattr(request.user, 'open_access_profile', None)
        if not profile or profile.course_id != lesson.course_id:
            from django.http import Http404
            raise Http404("Bu darsga kirish huquqingiz yo'q.")
    else:
        get_object_or_404(GroupMembership, group=lesson.group, student=request.user, is_active=True)
    return lesson


@role_required('student')
def student_group_lessons_view(request, group_id):
    membership = _student_membership_or_404(request, group_id)
    lessons = membership.group.lessons.all()
    lesson_rows = []
    for lesson in lessons:
        score = compute_homework_score(lesson.homework, request.user)
        lesson_rows.append({'lesson': lesson, 'score': score})

    exams = membership.group.control_exams.all()
    exam_rows = []
    for exam in exams:
        score_obj = ControlExamScore.objects.filter(exam=exam, student=request.user).first()
        exam_rows.append({'exam': exam, 'score_obj': score_obj})

    context = {'group': membership.group, 'lesson_rows': lesson_rows, 'exam_rows': exam_rows}
    return render(request, 'core/student_group_lessons.html', context)


@role_required('student')
def submit_control_exam_view(request, group_id, exam_id):
    membership = _student_membership_or_404(request, group_id)
    exam = get_object_or_404(ControlExam, id=exam_id, group=membership.group)
    score_obj, _ = ControlExamScore.objects.get_or_create(exam=exam, student=request.user)

    if score_obj.score is not None:
        messages.error(request, "Bu nazorat ishi allaqachon baholangan, qayta yuklab bo'lmaydi.")
        return redirect('student_group_lessons', group_id=group_id)

    if request.method == 'POST':
        form = ControlExamAnswerForm(request.POST, request.FILES, instance=score_obj)
        if form.is_valid():
            form.save()
            log_activity(request.user, f'"{exam.title}" nazorat ishiga javob yukladi')
            messages.success(request, 'Javobingiz yuklandi. Admin tekshirib, ball qo\'yadi.')
            # AI taklifini fon jarayonida tayyorlab qo'yamiz (Admin baholashga
            # kirganda tayyor turishi uchun) — talabani kutdirmaslik uchun thread'da.
            threading.Thread(target=grade_control_exam_score, args=(score_obj,), daemon=True).start()
    return redirect('student_group_lessons', group_id=group_id)


@role_required('student', 'open_access')
def student_lesson_view(request, lesson_id):
    lesson = _student_lesson_or_404(request, lesson_id)
    homework = lesson.homework
    student = request.user

    video_part = getattr(homework, 'video_part', None)
    video_done = bool(video_part and VideoProgress.objects.filter(video_part=video_part, student=student).exists())

    task_rows = []
    for level in homework.task_levels.all():
        sub = TaskSubmission.objects.filter(task_level=level, student=student).first()
        task_rows.append({
            'level': level,
            'submission': sub,
            'is_unlocked': bool(sub and sub.is_unlocked),
        })

    questions = homework.questions.all()
    my_answers_map = {a.question_id: a.answer_text for a in QuestionAnswer.objects.filter(question__homework=homework, student=student)}
    question_rows = [{'question': q, 'answer_text': my_answers_map.get(q.id, '')} for q in questions]

    quiz_questions = homework.quiz_questions.all()
    quiz_result = QuizResult.objects.filter(homework=homework, student=student).first()

    questions_grade = HomeworkGrade.objects.filter(homework=homework, student=student).first()
    questions_graded = bool(questions_grade and questions_grade.questions_score is not None)

    score = compute_homework_score(homework, student)

    context = {
        'lesson': lesson,
        'homework': homework,
        'video_part': video_part,
        'video_done': video_done,
        'task_rows': task_rows,
        'questions': questions,
        'question_rows': question_rows,
        'questions_graded': questions_graded,
        'quiz_questions': quiz_questions,
        'quiz_result': quiz_result,
        'score': score,
    }
    return render(request, 'core/student_lesson.html', context)


@role_required('student', 'open_access')
def mark_video_watched_view(request, lesson_id):
    lesson = _student_lesson_or_404(request, lesson_id)
    video_part = getattr(lesson.homework, 'video_part', None)
    if request.method == 'POST' and video_part:
        VideoProgress.objects.get_or_create(video_part=video_part, student=request.user)
        if request.user.role == 'open_access':
            # Open Access talabalari uchun kirish kodi yo'q — video ko'rilgach
            # barcha topshiriq darajalari avtomatik ochiladi.
            for level in lesson.homework.task_levels.all():
                sub, _ = TaskSubmission.objects.get_or_create(task_level=level, student=request.user)
                if not sub.unlocked_at:
                    sub.unlocked_at = timezone.now()
                    sub.save(update_fields=['unlocked_at'])
        messages.success(request, "Video ko'rildi deb belgilandi (+5 ball). Endi topshiriq qismi ochildi.")
    return redirect('student_lesson', lesson_id=lesson.id)


@role_required('student', 'open_access')
def unlock_task_view(request, lesson_id, level):
    lesson = _student_lesson_or_404(request, lesson_id)
    video_part = getattr(lesson.homework, 'video_part', None)
    video_done = bool(video_part and VideoProgress.objects.filter(video_part=video_part, student=request.user).exists())
    if not video_done:
        messages.error(request, "Avval video darsni to'liq ko'ring.")
        return redirect('student_lesson', lesson_id=lesson.id)

    task_level = get_object_or_404(TaskLevel, homework=lesson.homework, level=level)
    if request.method == 'POST':
        form = AccessCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip()
            if task_level.access_code and code == task_level.access_code:
                sub, _ = TaskSubmission.objects.get_or_create(task_level=task_level, student=request.user)
                if not sub.unlocked_at:
                    sub.unlocked_at = timezone.now()
                    sub.save()
                messages.success(request, f"{task_level.get_level_display()} topshiriq ochildi.")
            else:
                messages.error(request, "Kirish kodi noto'g'ri.")
    return redirect('student_lesson', lesson_id=lesson.id)


@role_required('student', 'open_access')
def submit_task_view(request, lesson_id, level):
    lesson = _student_lesson_or_404(request, lesson_id)
    task_level = get_object_or_404(TaskLevel, homework=lesson.homework, level=level)
    sub = get_object_or_404(TaskSubmission, task_level=task_level, student=request.user)
    if not sub.is_unlocked:
        messages.error(request, 'Avval kirish kodini kiriting.')
        return redirect('student_lesson', lesson_id=lesson.id)
    if sub.score is not None:
        messages.error(request, "Bu topshiriq allaqachon baholangan, qayta yuklab bo'lmaydi.")
        return redirect('student_lesson', lesson_id=lesson.id)
    if request.method == 'POST':
        form = TaskAnswerUploadForm(request.POST, request.FILES, instance=sub)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.submitted_at = timezone.now()
            obj.save()
            is_open_access = (request.user.role == 'open_access')
            if is_open_access:
                messages.success(
                    request,
                    f"{task_level.get_level_display()} topshiriq javobi yuklandi. AI baholamoqda...",
                )
            else:
                messages.success(request, f"{task_level.get_level_display()} topshiriq javobi yuklandi.")
            # AI baholashni fon jarayonida ishga tushiramiz — talabani kutdirmaslik uchun.
            # Open Access uchun natija to'g'ridan-to'g'ri yakuniy ball bo'ladi (auto_finalize),
            # oddiy talaba uchun esa faqat o'qituvchiga taklif sifatida ko'rinadi.
            threading.Thread(
                target=grade_task_submission, args=(obj,), kwargs={'auto_finalize': is_open_access}, daemon=True,
            ).start()
    return redirect('student_lesson', lesson_id=lesson.id)


@role_required('student', 'open_access')
def submit_questions_view(request, lesson_id):
    lesson = _student_lesson_or_404(request, lesson_id)
    homework = lesson.homework

    grade = HomeworkGrade.objects.filter(homework=homework, student=request.user).first()
    if grade and grade.questions_score is not None:
        messages.error(request, "Bu qism allaqachon baholangan, javoblarni qayta yuborib bo'lmaydi.")
        return redirect('student_lesson', lesson_id=lesson.id)

    if request.method == 'POST':
        for question in homework.questions.all():
            field_name = f'answer_{question.id}'
            text = request.POST.get(field_name, '').strip()
            if text:
                QuestionAnswer.objects.update_or_create(
                    question=question, student=request.user, defaults={'answer_text': text},
                )
        log_activity(request.user, f'"{lesson.title}" darsi savollariga javob yozdi')
        if request.user.role == 'open_access':
            # Open Access uchun 3-qism va faollikni AI to'liq avtomatik baholaydi.
            threading.Thread(target=grade_homework_questions, args=(homework, request.user), daemon=True).start()
            messages.success(request, 'Javoblaringiz saqlandi. AI ularni baholamoqda, natija tez orada tayyor bo\'ladi.')
        else:
            messages.success(request, 'Javoblaringiz saqlandi. O\'qituvchi tekshirib, ball qo\'yadi.')
    return redirect('student_lesson', lesson_id=lesson.id)


@role_required('student', 'open_access')
def submit_quiz_view(request, lesson_id):
    lesson = _student_lesson_or_404(request, lesson_id)
    homework = lesson.homework
    existing = QuizResult.objects.filter(homework=homework, student=request.user).first()
    if existing:
        messages.info(request, 'Siz bu quizni allaqachon topshirgansiz.')
        return redirect('student_lesson', lesson_id=lesson.id)

    quiz_questions = list(homework.quiz_questions.all())
    if request.method == 'POST' and quiz_questions:
        correct_count = 0
        for q in quiz_questions:
            selected = request.POST.get(f'quiz_{q.id}', '')
            is_correct = (selected == q.correct_option)
            if is_correct:
                correct_count += 1
            if selected:
                QuizAnswer.objects.update_or_create(
                    quiz_question=q, student=request.user,
                    defaults={'selected_option': selected, 'is_correct': is_correct},
                )
        total = len(quiz_questions)
        score = round((correct_count / total) * homework.QUIZ_SCORE, 1) if total else 0
        QuizResult.objects.create(
            homework=homework, student=request.user,
            correct_count=correct_count, total_count=total, score=score,
        )
        log_activity(request.user, f'"{lesson.title}" darsi quizini topshirdi ({correct_count}/{total})')
        messages.success(request, f'Quiz natijasi: {correct_count}/{total} — {score} ball')
    return redirect('student_lesson', lesson_id=lesson.id)


@role_required('observer')
def observer_dashboard_view(request):
    student = request.user.observed_student
    if not student:
        return render(request, 'core/observer_dashboard.html', {'student': None})

    memberships = student.group_memberships.filter(is_active=True).select_related('group')
    groups_data = []
    for m in memberships:
        rows = []
        for lesson in m.group.lessons.all():
            score = compute_homework_score(lesson.homework, student)
            rows.append({'lesson': lesson, 'score': score})
        exam_rows = []
        for exam in m.group.control_exams.all():
            score_obj = ControlExamScore.objects.filter(exam=exam, student=student).first()
            exam_rows.append({
                'exam': exam,
                'score': score_obj.score if (score_obj and score_obj.score is not None) else None,
            })
        groups_data.append({'group': m.group, 'rows': rows, 'exam_rows': exam_rows})

    confirmation = ObserverConfirmation.objects.filter(observer=request.user, student=student).first()
    latest_update = get_latest_grade_update(student)
    is_stale = bool(confirmation and latest_update and latest_update > confirmation.confirmed_at)
    context = {
        'student': student, 'groups_data': groups_data,
        'confirmation': confirmation, 'is_stale': is_stale,
    }
    return render(request, 'core/observer_dashboard.html', context)


@role_required('observer')
def observer_rating_view(request, group_id):
    student = request.user.observed_student
    membership = get_object_or_404(GroupMembership, group_id=group_id, student=student, is_active=True)
    group = membership.group
    members = group.memberships.filter(is_active=True).select_related('student')
    lessons = list(group.lessons.all())
    exams = list(group.control_exams.all())

    rating_rows = []
    for m in members:
        lesson_total = sum(compute_homework_score(l.homework, m.student)['total'] for l in lessons)
        exam_total = 0
        for exam in exams:
            score_obj = ControlExamScore.objects.filter(exam=exam, student=m.student).first()
            exam_total += score_obj.score if (score_obj and score_obj.score is not None) else 0
        rating_rows.append({
            'student': m.student, 'lesson_total': lesson_total,
            'exam_total': exam_total, 'grand_total': lesson_total + exam_total,
        })
    rating_rows.sort(key=lambda r: r['grand_total'], reverse=True)

    context = {
        'group': group, 'rating_rows': rating_rows, 'lesson_count': len(lessons),
        'exam_count': len(exams), 'observed_student': student,
    }
    return render(request, 'core/observer_rating.html', context)


@role_required('observer')
def confirm_review_view(request):
    student = request.user.observed_student
    if request.method == 'POST' and student:
        ObserverConfirmation.objects.update_or_create(observer=request.user, student=student)
        messages.success(request, "Tanishib chiqganingiz qayd etildi. Rahmat!")
    return redirect('observer_dashboard')


# ============================================================
#  ADMIN — MONITORING (Kuzatuvchilar nazorati)
# ============================================================

@role_required('admin')
def monitoring_view(request):
    groups = Group.objects.select_related('course').all()
    group_rows = []
    for group in groups:
        needs_attention = 0
        memberships = group.memberships.filter(is_active=True).select_related('student')
        for m in memberships:
            student = m.student
            observers = student.observers.all()
            if not observers:
                continue
            latest_update = get_latest_grade_update(student)
            for obs in observers:
                confirmation = ObserverConfirmation.objects.filter(observer=obs, student=student).first()
                is_stale = bool(confirmation and latest_update and latest_update > confirmation.confirmed_at)
                if not confirmation or is_stale:
                    needs_attention += 1
        group_rows.append({'group': group, 'needs_attention': needs_attention})
    return render(request, 'core/monitoring.html', {'group_rows': group_rows})


@role_required('admin')
def monitoring_group_detail_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    memberships = group.memberships.filter(is_active=True).select_related('student')
    rows = []
    for m in memberships:
        student = m.student
        last_lesson = group.lessons.order_by('-created_at').first()
        last_score = None
        if last_lesson:
            last_score = compute_homework_score(last_lesson.homework, student)
        latest_update = get_latest_grade_update(student)
        observers = student.observers.all()
        if observers:
            for obs in observers:
                confirmation = ObserverConfirmation.objects.filter(observer=obs, student=student).first()
                is_stale = bool(confirmation and latest_update and latest_update > confirmation.confirmed_at)
                rows.append({
                    'student': student, 'observer': obs, 'last_lesson': last_lesson,
                    'last_score': last_score, 'confirmation': confirmation, 'is_stale': is_stale,
                })
        else:
            rows.append({
                'student': student, 'observer': None, 'last_lesson': last_lesson,
                'last_score': last_score, 'confirmation': None, 'is_stale': False,
            })
    return render(request, 'core/monitoring_group_detail.html', {'group': group, 'rows': rows})


@role_required('student')
def student_grades_view(request):
    memberships = request.user.group_memberships.filter(is_active=True).select_related('group')
    groups_data = []
    for m in memberships:
        rows = []
        for lesson in m.group.lessons.all():
            score = compute_homework_score(lesson.homework, request.user)
            rows.append({'lesson': lesson, 'score': score})
        groups_data.append({'group': m.group, 'rows': rows})
    return render(request, 'core/student_grades.html', {'groups_data': groups_data})


@role_required('student')
def student_rating_view(request, group_id):
    membership = _student_membership_or_404(request, group_id)
    group = membership.group
    members = group.memberships.filter(is_active=True).select_related('student')
    lessons = list(group.lessons.all())
    exams = list(group.control_exams.all())

    rating_rows = []
    for m in members:
        lesson_total = sum(compute_homework_score(l.homework, m.student)['total'] for l in lessons)
        exam_total = 0
        for exam in exams:
            score_obj = ControlExamScore.objects.filter(exam=exam, student=m.student).first()
            exam_total += score_obj.score if (score_obj and score_obj.score is not None) else 0
        rating_rows.append({
            'student': m.student,
            'lesson_total': lesson_total,
            'exam_total': exam_total,
            'grand_total': lesson_total + exam_total,
        })
    rating_rows.sort(key=lambda r: r['grand_total'], reverse=True)

    context = {'group': group, 'rating_rows': rating_rows, 'lesson_count': len(lessons), 'exam_count': len(exams)}
    return render(request, 'core/student_rating.html', context)


@role_required('student')
def student_certificates_view(request):
    certificates = request.user.certificates.select_related('group', 'group__course')
    return render(request, 'core/student_certificates.html', {'certificates': certificates})


@role_required('student')
def certificate_detail_view(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, student=request.user)
    return render(request, 'core/certificate_detail.html', {'certificate': certificate})


# ============================================================
#  O'QITUVCHI — UYGA VAZIFANI BAHOLASH
# ============================================================

@role_required('teacher')
def grade_homework_list_view(request, lesson_id):
    lesson = _teacher_lesson_or_404(request, lesson_id)
    members = lesson.group.memberships.filter(is_active=True).select_related('student')
    rows = []
    for m in members:
        score = compute_homework_score(lesson.homework, m.student)
        rows.append({'student': m.student, 'score': score})
    return render(request, 'core/grade_homework_list.html', {'lesson': lesson, 'rows': rows})


@role_required('teacher')
def grade_student_homework_view(request, lesson_id, student_id):
    lesson = _teacher_lesson_or_404(request, lesson_id)
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    homework = lesson.homework

    video_part = getattr(homework, 'video_part', None)
    video_done = bool(video_part and VideoProgress.objects.filter(video_part=video_part, student=student).exists())

    task_rows = []
    for level in homework.task_levels.all():
        sub = TaskSubmission.objects.filter(task_level=level, student=student).first()
        task_rows.append({'level': level, 'submission': sub})

    quiz_result = QuizResult.objects.filter(homework=homework, student=student).first()
    grade, _ = HomeworkGrade.objects.get_or_create(homework=homework, student=student)

    if request.method == 'POST':
        for row in task_rows:
            sub = row['submission']
            if not sub or not sub.answer_file:
                continue
            field_name = f"task_{row['level'].level}"
            raw = request.POST.get(field_name, '').strip()
            if raw == '':
                continue
            try:
                value = int(raw)
            except ValueError:
                continue
            value = max(0, min(value, row['level'].max_score))
            sub.score = value
            sub.graded_by = request.user
            sub.graded_at = timezone.now()
            sub.save()

        grade_form = HomeworkGradeForm(request.POST, instance=grade)
        if grade_form.is_valid():
            g = grade_form.save(commit=False)
            g.homework = homework
            g.student = student
            g.graded_by = request.user
            g.graded_at = timezone.now()
            g.save()

        log_activity(
            request.user,
            f'{student.get_full_name()} ning "{lesson.title}" uyga vazifasini baholadi',
        )
        messages.success(request, 'Baholar saqlandi')
        return redirect('grade_student_homework', lesson_id=lesson.id, student_id=student.id)

    grade_form = HomeworkGradeForm(instance=grade)
    score = compute_homework_score(homework, student)
    answers_map = {a.question_id: a.answer_text for a in QuestionAnswer.objects.filter(question__homework=homework, student=student)}
    question_rows = [{'question': q, 'answer_text': answers_map.get(q.id, '')} for q in homework.questions.all()]

    context = {
        'lesson': lesson, 'student': student, 'video_done': video_done,
        'task_rows': task_rows, 'quiz_result': quiz_result, 'grade_form': grade_form,
        'question_rows': question_rows,
        'score': score,
    }
    return render(request, 'core/grade_student_homework.html', context)


# ============================================================
#  ADMIN — SERTIFIKAT BERISH
# ============================================================

@role_required('admin')
def issue_certificate_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    members = group.memberships.filter(is_active=True).select_related('student')
    issued_ids = set(Certificate.objects.filter(group=group).values_list('student_id', flat=True))

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
        Certificate.objects.get_or_create(student=student, group=group, defaults={'issued_by': request.user})
        log_activity(request.user, f"{student.get_full_name()} ga {group.name} guruhi uchun sertifikat berdi")
        messages.success(request, f"{student.get_full_name()} ga sertifikat berildi")
        return redirect('issue_certificate', group_id=group.id)

    context = {'group': group, 'members': members, 'issued_ids': issued_ids}
    return render(request, 'core/issue_certificate.html', context)
