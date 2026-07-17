from django.contrib import admin
from .models import (
    Certificate, ControlExam, ControlExamScore, Course, Group, GroupMembership, Homework,
    HomeworkGrade, HomeworkQuestion, HomeworkVideo, Lesson, ObserverConfirmation, QuestionAnswer,
    QuizAnswer, QuizQuestion, QuizResult, ShowcaseCard, TaskLevel, TaskSubmission, VideoProgress,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'teacher', 'created_by', 'is_active')
    list_filter = ('course', 'is_active')
    search_fields = ('name',)


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'added_by', 'is_active', 'joined_at')
    list_filter = ('group', 'is_active')
    search_fields = ('student__username', 'student__first_name', 'student__last_name')


@admin.register(ControlExam)
class ControlExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'max_score', 'created_by', 'created_at')
    list_filter = ('group',)


@admin.register(ControlExamScore)
class ControlExamScoreAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'graded_by', 'graded_at')
    list_filter = ('exam',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'created_at', 'order')
    list_filter = ('group',)


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'created_at')


@admin.register(HomeworkVideo)
class HomeworkVideoAdmin(admin.ModelAdmin):
    list_display = ('homework', 'video_url')


@admin.register(TaskLevel)
class TaskLevelAdmin(admin.ModelAdmin):
    list_display = ('homework', 'level', 'access_code')
    list_filter = ('level',)


@admin.register(HomeworkQuestion)
class HomeworkQuestionAdmin(admin.ModelAdmin):
    list_display = ('homework', 'text', 'order')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('homework', 'text', 'correct_option', 'order')


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'video_part', 'completed_at')


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'task_level', 'unlocked_at', 'submitted_at', 'score')


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'submitted_at')


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'homework', 'correct_count', 'total_count', 'score')


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz_question', 'selected_option', 'is_correct')


@admin.register(HomeworkGrade)
class HomeworkGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'homework', 'questions_score', 'activity_score', 'graded_by')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'issued_by', 'issued_at')


@admin.register(ObserverConfirmation)
class ObserverConfirmationAdmin(admin.ModelAdmin):
    list_display = ('observer', 'student', 'confirmed_at')


@admin.register(ShowcaseCard)
class ShowcaseCardAdmin(admin.ModelAdmin):
    list_display = ('slot', 'button_label', 'title', 'updated_by', 'updated_at')
