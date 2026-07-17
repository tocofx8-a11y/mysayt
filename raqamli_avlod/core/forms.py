from django import forms
from accounts.models import User
from .models import (
    Course, ControlExam, ControlExamScore, Group, GroupMembership, Homework, HomeworkGrade,
    HomeworkQuestion, HomeworkVideo, Lesson, QuizQuestion, ShowcaseCard, TaskLevel, TaskSubmission,
)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'description')
        labels = {'name': 'Kurs nomi', 'description': 'Tavsif'}


class ShowcaseCardForm(forms.ModelForm):
    class Meta:
        model = ShowcaseCard
        fields = ('button_label', 'title', 'content', 'icon_image', 'word_file')
        labels = {
            'button_label': 'Tugma matni',
            'title': 'Sarlavha',
            'content': 'Matn',
            'icon_image': 'Tugma rasmi (ixtiyoriy)',
            'word_file': 'Word fayldan matn olish (ixtiyoriy)',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'course', 'teacher')
        labels = {'name': 'Guruh nomi', 'course': 'Kurs', 'teacher': "O'qituvchi"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        teacher_qs = User.objects.filter(role=User.Role.TEACHER, is_active=True)
        # Guruh tahrirlanayotganda, joriy o'qituvchi faolsizlantirilgan bo'lsa ham
        # ro'yxatda ko'rinib tursin (aks holda tanlov yo'qolib qoladi).
        if self.instance and self.instance.pk and self.instance.teacher_id:
            teacher_qs = teacher_qs | User.objects.filter(id=self.instance.teacher_id)
        self.fields['teacher'].queryset = teacher_qs.distinct()
        self.fields['teacher'].required = False


class AddStudentToGroupForm(forms.Form):
    """Admin talabani mavjud guruhga biriktirishi uchun."""
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.STUDENT, is_active=True),
        label='Talaba',
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.filter(is_active=True),
        label='Guruh',
    )


class ControlExamForm(forms.ModelForm):
    class Meta:
        model = ControlExam
        fields = ('title', 'description', 'attachment', 'max_score')
        labels = {
            'title': 'Nomi',
            'description': 'Tavsif / savollar matni',
            'attachment': 'Fayl (ixtiyoriy)',
            'max_score': 'Maksimal ball',
        }


class ControlExamAnswerForm(forms.ModelForm):
    """Talaba nazorat ishiga javob faylini yuklashi uchun."""
    class Meta:
        model = ControlExamScore
        fields = ('answer_file',)
        labels = {'answer_file': 'Javob fayli'}


class ControlExamAnswerForm(forms.ModelForm):
    """Talaba nazorat ishiga javob faylini yuklashi uchun."""
    class Meta:
        model = ControlExamScore
        fields = ('answer_file',)
        labels = {'answer_file': 'Javob fayli (.txt, .pdf, .docx)'}


# ============================================================
#  DARSLAR VA UYGA VAZIFA FORMALARI (O'qituvchi paneli uchun)
# ============================================================

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title', 'lecture_text', 'lecture_file', 'order')
        labels = {
            'title': 'Dars mavzusi', 'lecture_text': 'Maruza matni',
            'lecture_file': 'Maruza fayli (ixtiyoriy)', 'order': 'Tartib raqami',
        }
        widgets = {'lecture_text': forms.Textarea(attrs={'rows': 8})}


class HomeworkVideoForm(forms.ModelForm):
    class Meta:
        model = HomeworkVideo
        fields = ('video_url', 'video_file')
        labels = {'video_url': 'Video havolasi (YouTube va h.k.)', 'video_file': 'Yoki video fayl yuklash'}


class TaskLevelForm(forms.ModelForm):
    class Meta:
        model = TaskLevel
        fields = ('instructions', 'access_code')
        labels = {'instructions': 'Topshiriq matni', 'access_code': 'Kirish kodi'}
        widgets = {'instructions': forms.Textarea(attrs={'rows': 5})}


class HomeworkQuestionForm(forms.ModelForm):
    class Meta:
        model = HomeworkQuestion
        fields = ('text', 'order')
        labels = {'text': 'Savol matni', 'order': 'Tartib raqami'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ('text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'order')
        labels = {
            'text': 'Savol matni', 'option_a': 'A variant', 'option_b': 'B variant',
            'option_c': 'C variant', 'option_d': 'D variant',
            'correct_option': "To'g'ri javob", 'order': 'Tartib raqami',
        }
        widgets = {'text': forms.Textarea(attrs={'rows': 2})}


# ============================================================
#  TALABA PANELI FORMALARI
# ============================================================

class AccessCodeForm(forms.Form):
    """Talaba topshiriq darajasini ochish uchun kod kiritadi."""
    code = forms.CharField(label='Kirish kodi', max_length=50)


class TaskAnswerUploadForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ('answer_file',)
        labels = {'answer_file': 'Javob fayli (.txt, .pdf, .docx)'}


class QuestionAnswerForm(forms.Form):
    """Har bir savol uchun dinamik javob maydoni yaratiladi (view ichida)."""
    pass


class HomeworkGradeForm(forms.ModelForm):
    class Meta:
        model = HomeworkGrade
        fields = ('questions_score', 'activity_score')
        labels = {'questions_score': '3-qism (savol-javob) ball, 0-10', 'activity_score': 'Faollik ball, 0-10'}
