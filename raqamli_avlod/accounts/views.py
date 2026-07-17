from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .decorators import role_required
from .forms import (
    ObserverCreationForm, ObserverEditForm, OpenAccessRegisterForm, StaffCreationForm,
    StaffEditForm, StudentCreationForm,
)
from .models import User, log_activity


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('register_form', OpenAccessRegisterForm())
        return context


def open_access_register_view(request):
    """
    Kirish sahifasidagi "Ro'yxatdan o'tish" tugmasi orqali ochiladigan
    forma. Muvaffaqiyatli bo'lsa, foydalanuvchi avtomatik tizimga kirib,
    o'z Open Access paneliga yo'naltiriladi.
    """
    if request.method != 'POST':
        return redirect('login')

    form = OpenAccessRegisterForm(request.POST)
    if form.is_valid():
        new_user = form.save()
        log_activity(
            new_user,
            f"Open Access sifatida ro'yxatdan o'tdi ({new_user.open_access_profile.course.name} kursi)",
        )
        auth_login(request, new_user)
        messages.success(request, f"Xush kelibsiz, {new_user.get_full_name()}!")
        return redirect('open_access_dashboard')

    # Xatolik bo'lsa, login sahifasini "Ro'yxatdan o'tish" oynasi ochiq
    # holda, xatolar bilan qayta ko'rsatamiz.
    from django.contrib.auth.forms import AuthenticationForm
    return render(
        request,
        'accounts/login.html',
        {'form': AuthenticationForm(), 'register_form': form, 'register_open': True},
    )


@login_required
def dashboard_redirect(request):
    """
    Foydalanuvchi tizimga kirgandan so'ng, roliga qarab
    tegishli panelga yo'naltiriladi.
    (Har bir panel keyingi bosqichlarda yaratiladi.)
    """
    user = request.user
    if user.is_super_admin:
        return redirect('superadmin_dashboard')
    if user.is_admin_role:
        return redirect('admin_dashboard')
    if user.is_teacher:
        return redirect('teacher_dashboard')
    if user.is_student:
        return redirect('student_dashboard')
    if user.is_observer:
        return redirect('observer_dashboard')
    if user.is_open_access:
        return redirect('open_access_dashboard')
    return redirect('login')


@role_required('super_admin')
def create_staff_view(request):
    """Super Admin bu orqali Admin yoki O'qituvchi ro'yxatdan o'tkazadi."""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(created_by=request.user)
            role_label = new_user.get_role_display()
            log_activity(
                request.user,
                f"{role_label} sifatida {new_user.get_full_name()} ({new_user.username}) ni ro'yxatdan o'tkazdi",
            )
            messages.success(request, f"{role_label} muvaffaqiyatli yaratildi: {new_user.username}")
            return redirect('superadmin_dashboard')
    else:
        form = StaffCreationForm()
    return render(request, 'accounts/create_staff.html', {'form': form})


@role_required('super_admin')
def edit_staff_view(request, user_id):
    """Super Admin mavjud Admin/O'qituvchi ma'lumotlarini tahrirlaydi."""
    staff = get_object_or_404(User, id=user_id, role__in=[User.Role.ADMIN, User.Role.TEACHER])
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"{staff.get_role_display()} {staff.get_full_name()} ma'lumotlarini tahrirladi")
            messages.success(request, "Ma'lumotlar yangilandi")
            return redirect('superadmin_dashboard')
    else:
        form = StaffEditForm(instance=staff)
    return render(request, 'accounts/edit_staff.html', {'form': form, 'staff': staff})


@role_required('super_admin')
def toggle_staff_active_view(request, user_id):
    """Super Admin Admin/O'qituvchini faolsizlantiradi (chiqarib yuboradi) yoki qayta faollashtiradi."""
    staff = get_object_or_404(User, id=user_id, role__in=[User.Role.ADMIN, User.Role.TEACHER])
    if request.method == 'POST':
        staff.is_active = not staff.is_active
        staff.save()
        holat = 'faollashtirdi' if staff.is_active else "chiqarib yubordi (faolsizlantirdi)"
        log_activity(request.user, f"{staff.get_role_display()} {staff.get_full_name()} ni {holat}")
        messages.success(
            request,
            f"{staff.get_full_name()} {'qayta faollashtirildi' if staff.is_active else 'chiqarib yuborildi'}",
        )
    return redirect('superadmin_dashboard')


@role_required('admin')
def register_student_view(request):
    """Admin bu orqali talabani ro'yxatga oladi (login/parol beradi)."""
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(created_by=request.user)
            log_activity(
                request.user,
                f"Talaba {new_user.get_full_name()} ({new_user.username}) ni ro'yxatdan o'tkazdi",
            )
            messages.success(
                request,
                f"Talaba yaratildi — login: {new_user.username}. Endi uni guruhga biriktiring.",
            )
            return redirect('admin_dashboard')
    else:
        form = StudentCreationForm()
    return render(request, 'accounts/register_student.html', {'form': form})


@role_required('admin')
def register_observer_view(request):
    """Admin bu orqali Kuzatuvchi (masalan ota-ona)ni ro'yxatga oladi va talabaga biriktiradi."""
    if request.method == 'POST':
        form = ObserverCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(created_by=request.user)
            log_activity(
                request.user,
                f"Kuzatuvchi {new_user.get_full_name()} ({new_user.username}) ni "
                f"{new_user.observed_student.get_full_name()} talabaga biriktirib ro'yxatdan o'tkazdi",
            )
            messages.success(request, f"Kuzatuvchi yaratildi — login: {new_user.username}")
            return redirect('admin_dashboard')
    else:
        form = ObserverCreationForm()
    return render(request, 'accounts/register_observer.html', {'form': form})


@role_required('admin')
def edit_student_view(request, user_id):
    """Admin mavjud talaba ma'lumotlarini tahrirlaydi."""
    student = get_object_or_404(User, id=user_id, role=User.Role.STUDENT)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Talaba {student.get_full_name()} ma'lumotlarini tahrirladi")
            messages.success(request, "Ma'lumotlar yangilandi")
            return redirect('admin_dashboard')
    else:
        form = StaffEditForm(instance=student)
    return render(request, 'accounts/edit_student.html', {'form': form, 'staff': student})


@role_required('admin')
def toggle_student_active_view(request, user_id):
    """Admin talabani faolsizlantiradi (chiqarib yuboradi) yoki qayta faollashtiradi."""
    student = get_object_or_404(User, id=user_id, role=User.Role.STUDENT)
    if request.method == 'POST':
        student.is_active = not student.is_active
        student.save()
        holat = 'faollashtirdi' if student.is_active else "chiqarib yubordi (faolsizlantirdi)"
        log_activity(request.user, f"Talaba {student.get_full_name()} ni {holat}")
        messages.success(
            request,
            f"{student.get_full_name()} {'qayta faollashtirildi' if student.is_active else 'chiqarib yuborildi'}",
        )
    return redirect('admin_dashboard')


@role_required('admin')
def edit_observer_view(request, user_id):
    """Admin mavjud kuzatuvchi ma'lumotlarini va biriktirilgan talabasini tahrirlaydi."""
    observer = get_object_or_404(User, id=user_id, role=User.Role.OBSERVER)
    if request.method == 'POST':
        form = ObserverEditForm(request.POST, instance=observer)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Kuzatuvchi {observer.get_full_name()} ma'lumotlarini tahrirladi")
            messages.success(request, "Ma'lumotlar yangilandi")
            return redirect('admin_dashboard')
    else:
        form = ObserverEditForm(instance=observer)
    return render(request, 'accounts/edit_observer.html', {'form': form, 'staff': observer})


@role_required('admin')
def toggle_observer_active_view(request, user_id):
    """Admin kuzatuvchini faolsizlantiradi (chiqarib yuboradi) yoki qayta faollashtiradi."""
    observer = get_object_or_404(User, id=user_id, role=User.Role.OBSERVER)
    if request.method == 'POST':
        observer.is_active = not observer.is_active
        observer.save()
        holat = 'faollashtirdi' if observer.is_active else "chiqarib yubordi (faolsizlantirdi)"
        log_activity(request.user, f"Kuzatuvchi {observer.get_full_name()} ni {holat}")
        messages.success(
            request,
            f"{observer.get_full_name()} {'qayta faollashtirildi' if observer.is_active else 'chiqarib yuborildi'}",
        )
    return redirect('admin_dashboard')
