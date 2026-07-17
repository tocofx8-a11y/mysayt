from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('open-access/register/', views.open_access_register_view, name='open_access_register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('staff/create/', views.create_staff_view, name='create_staff'),
    path('staff/<int:user_id>/edit/', views.edit_staff_view, name='edit_staff'),
    path('staff/<int:user_id>/toggle-active/', views.toggle_staff_active_view, name='toggle_staff_active'),
    path('student/register/', views.register_student_view, name='register_student'),
    path('student/<int:user_id>/edit/', views.edit_student_view, name='edit_student'),
    path('student/<int:user_id>/toggle-active/', views.toggle_student_active_view, name='toggle_student_active'),
    path('observer/register/', views.register_observer_view, name='register_observer'),
    path('observer/<int:user_id>/edit/', views.edit_observer_view, name='edit_observer'),
    path('observer/<int:user_id>/toggle-active/', views.toggle_observer_active_view, name='toggle_observer_active'),
]
