"""
Uyga vazifa uchun umumiy ballni hisoblovchi yordamchi funksiya.
Bir joyda saqlanadi, chunki bu hisob-kitob bir nechta joyda
(Baholarim, Reyting, O'qituvchi baholash sahifasi) ishlatiladi.
"""
from .models import ControlExamScore, GroupMembership, HomeworkGrade, Lesson, QuizResult, TaskSubmission, VideoProgress


def compute_homework_score(homework, student):
    video_part = getattr(homework, 'video_part', None)
    video_score = 0
    if video_part and VideoProgress.objects.filter(video_part=video_part, student=student).exists():
        video_score = homework.VIDEO_SCORE

    task_breakdown = {}
    task_score = 0
    for level in homework.task_levels.all():
        sub = TaskSubmission.objects.filter(task_level=level, student=student).first()
        score = sub.score if (sub and sub.score is not None) else 0
        task_breakdown[level.level] = {
            'label': level.get_level_display(),
            'max_score': level.max_score,
            'score': score,
            'submitted': bool(sub and sub.answer_file),
        }
        task_score += score

    quiz_result = QuizResult.objects.filter(homework=homework, student=student).first()
    quiz_score = quiz_result.score if quiz_result else 0

    grade = HomeworkGrade.objects.filter(homework=homework, student=student).first()
    questions_score = grade.questions_score if (grade and grade.questions_score is not None) else 0
    activity_score = grade.activity_score if (grade and grade.activity_score is not None) else 0

    total = video_score + task_score + questions_score + quiz_score + activity_score

    return {
        'video_score': video_score,
        'task_score': task_score,
        'task_breakdown': task_breakdown,
        'questions_score': questions_score,
        'quiz_score': quiz_score,
        'quiz_result': quiz_result,
        'activity_score': activity_score,
        'total': total,
        'max_total': homework.VIDEO_SCORE + homework.TASK_TOTAL_SCORE + homework.QUESTIONS_SCORE + homework.QUIZ_SCORE + homework.ACTIVITY_SCORE,
    }


def get_latest_grade_update(student):
    """
    Talabaning faol guruhlari bo'yicha eng so'nggi "yangilanish" vaqtini topadi:
    yangi dars qo'shilganmi, biror qism baholanganmi, quiz topshirilganmi,
    yoki nazorat ishi bahosi qo'yilganmi — shulardan eng so'nggisi qaytariladi.

    Bu Kuzatuvchining "Tanishib chiqdim" tasdig'i eskirganmi (yangi baho
    qo'shilganmi) ekanini aniqlash uchun ishlatiladi.
    """
    memberships = GroupMembership.objects.filter(student=student, is_active=True)
    group_ids = list(memberships.values_list('group_id', flat=True))
    if not group_ids:
        return None

    timestamps = []

    lesson_latest = Lesson.objects.filter(group_id__in=group_ids).order_by('-created_at').values_list('created_at', flat=True).first()
    if lesson_latest:
        timestamps.append(lesson_latest)

    grade_latest = HomeworkGrade.objects.filter(
        student=student, graded_at__isnull=False
    ).order_by('-graded_at').values_list('graded_at', flat=True).first()
    if grade_latest:
        timestamps.append(grade_latest)

    task_latest = TaskSubmission.objects.filter(
        student=student, graded_at__isnull=False
    ).order_by('-graded_at').values_list('graded_at', flat=True).first()
    if task_latest:
        timestamps.append(task_latest)

    quiz_latest = QuizResult.objects.filter(student=student).order_by('-submitted_at').values_list('submitted_at', flat=True).first()
    if quiz_latest:
        timestamps.append(quiz_latest)

    exam_latest = ControlExamScore.objects.filter(
        student=student, graded_at__isnull=False
    ).order_by('-graded_at').values_list('graded_at', flat=True).first()
    if exam_latest:
        timestamps.append(exam_latest)

    return max(timestamps) if timestamps else None
