from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Foydalanish: @role_required('super_admin')
                 @role_required('admin', 'super_admin')
    Faqat ko'rsatilgan rolga(lar)ga ega foydalanuvchi sahifaga kira oladi,
    aks holda 403 (ruxsat yo'q) xatosi chiqadi.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied("Bu bo'limga kirish uchun ruxsatingiz yo'q.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
