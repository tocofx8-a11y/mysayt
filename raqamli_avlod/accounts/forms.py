from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class OpenAccessRegisterForm(UserCreationForm):
    """
    Kirish sahifasidan foydalanuvchi o'zi to'ldiradigan ro'yxatdan o'tish
    formasi. "Roli" o'rniga "Kursni tanlang" maydoni bo'ladi — tanlangan
    kurs bo'yicha Open Access profili yaratiladi.
    """
    first_name = forms.CharField(label='Ismi', required=True)
    last_name = forms.CharField(label='Familiyasi', required=True)
    phone = forms.CharField(label='Telefon raqami', required=False)
    course = forms.ModelChoiceField(
        queryset=None, label='Kursni tanlang', empty_label='— Kursni tanlang —',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'course')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Course
        self.fields['course'].queryset = Course.objects.filter(is_active=True)

    def save(self, commit=True):
        from core.models import OpenAccessProfile
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = User.Role.OPEN_ACCESS
        if commit:
            user.save()
            OpenAccessProfile.objects.create(user=user, course=self.cleaned_data['course'])
        return user


class StaffCreationForm(UserCreationForm):
    """
    Super Admin bu forma orqali Admin yoki O'qituvchi ro'yxatdan o'tkazadi.
    """
    ROLE_CHOICES = (
        (User.Role.ADMIN, 'Admin'),
        (User.Role.TEACHER, "O'qituvchi"),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Roli')
    first_name = forms.CharField(label='Ismi', required=True)
    last_name = forms.CharField(label='Familiyasi', required=True)
    phone = forms.CharField(label='Telefon raqami', required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'role')

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = self.cleaned_data['role']
        user.created_by = created_by
        if commit:
            user.save()
        return user


class StaffEditForm(forms.ModelForm):
    """Super Admin mavjud Admin/O'qituvchi ma'lumotlarini tahrirlashi uchun."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
        labels = {'first_name': 'Ismi', 'last_name': 'Familiyasi', 'phone': 'Telefon raqami'}


class StudentCreationForm(UserCreationForm):
    """
    Admin bu forma orqali talabani ro'yxatga oladi (login/parol berish).
    """
    first_name = forms.CharField(label='Ismi', required=True)
    last_name = forms.CharField(label='Familiyasi', required=True)
    phone = forms.CharField(label='Telefon raqami', required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone')

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = User.Role.STUDENT
        user.created_by = created_by
        if commit:
            user.save()
        return user


class ObserverCreationForm(UserCreationForm):
    """
    Admin bu forma orqali Kuzatuvchi (masalan ota-ona) ro'yxatga oladi va
    uni bitta talabaga biriktiradi.
    """
    first_name = forms.CharField(label='Ismi', required=True)
    last_name = forms.CharField(label='Familiyasi', required=True)
    phone = forms.CharField(label='Telefon raqami', required=False)
    observed_student = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.STUDENT, is_active=True),
        label='Qaysi talabani kuzatadi',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'observed_student')

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = User.Role.OBSERVER
        user.observed_student = self.cleaned_data['observed_student']
        user.created_by = created_by
        if commit:
            user.save()
        return user


class ObserverEditForm(forms.ModelForm):
    """Admin mavjud Kuzatuvchi ma'lumotlarini va biriktirilgan talabasini tahrirlashi uchun."""
    observed_student = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.STUDENT, is_active=True),
        label='Qaysi talabani kuzatadi',
        required=False,
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'observed_student')
        labels = {'first_name': 'Ismi', 'last_name': 'Familiyasi', 'phone': 'Telefon raqami'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tahrirlanayotgan kuzatuvchining hozirgi talabasi faolsizlantirilgan bo'lsa ham
        # ro'yxatda ko'rinib tursin.
        if self.instance and self.instance.pk and self.instance.observed_student_id:
            self.fields['observed_student'].queryset = (
                User.objects.filter(role=User.Role.STUDENT, is_active=True)
                | User.objects.filter(id=self.instance.observed_student_id)
            ).distinct()
