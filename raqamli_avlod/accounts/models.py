from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Tizimning barcha foydalanuvchilari shu model orqali boshqariladi.
    Rol (role) maydoni orqali foydalanuvchi 5 turdan biriga tegishli bo'ladi:
    Super Admin, Admin, O'qituvchi, Talaba, Kuzatuvchi.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        TEACHER = 'teacher', "O'qituvchi"
        STUDENT = 'student', 'Talaba'
        OBSERVER = 'observer', 'Kuzatuvchi'
        OPEN_ACCESS = 'open_access', 'Open Access'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        verbose_name='Roli',
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon raqami')

    # Faqat "Kuzatuvchi" rolidagi foydalanuvchilar uchun: qaysi talabani kuzatadi
    observed_student = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='observers',
        limit_choices_to={'role': 'student'},
        verbose_name='Kuzatilayotgan talaba',
    )

    # Telegram orqali kirish uchun (bot ulanganda to'ldiriladi)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name='Telegram ID')

    # Bu foydalanuvchini kim ro'yxatdan o'tkazgani (masalan: talabani qaysi Admin qo'shgan)
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users',
        verbose_name='Kim tomonidan yaratilgan',
    )

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    # --- Qulaylik uchun tekshiruv metodlari ---
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_observer(self):
        return self.role == self.Role.OBSERVER

    @property
    def is_open_access(self):
        return self.role == self.Role.OPEN_ACCESS

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'


class ActivityLog(models.Model):
    """
    Har bir muhim harakat shu yerga yoziladi, masalan:
    "Admin ALI 12:20da ANVARni G41 guruhga biriktirdi"
    "O'qituvchi Shaxnoza 13:00da uyga vazifani H45 guruhi uchun joylashtirdi"
    Bu bo'lim Super Admin panelida barcha admin va o'qituvchilar faoliyatini
    kuzatish uchun ishlatiladi.
    """

    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name="Harakatni bajargan foydalanuvchi",
    )
    description = models.TextField(verbose_name='Harakat tavsifi')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Vaqti')

    class Meta:
        verbose_name = 'Faoliyat logi'
        verbose_name_plural = 'Faoliyat loglari'
        ordering = ['-created_at']

    def __str__(self):
        vaqt = timezone.localtime(self.created_at).strftime('%H:%M')
        return f'{self.actor.get_role_display()} {self.actor.get_full_name() or self.actor.username} {vaqt}da: {self.description}'


def log_activity(actor, description):
    """
    Loyihaning istalgan joyidan chaqiriladigan yordamchi funksiya.
    Masalan: log_activity(request.user, "ANVARni G41 guruhga biriktirdi")
    """
    return ActivityLog.objects.create(actor=actor, description=description)
