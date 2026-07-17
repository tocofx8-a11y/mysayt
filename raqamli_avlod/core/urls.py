from django.urls import path
from . import views

urlpatterns = [
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/course/create/', views.create_course_view, name='create_course'),
    path('superadmin/course/<int:course_id>/edit/', views.edit_course_view, name='edit_course'),
    path('superadmin/showcase/', views.showcase_list_view, name='showcase_list'),
    path('superadmin/showcase/<int:card_id>/edit/', views.edit_showcase_view, name='edit_showcase'),
    path('superadmin/group/create/', views.create_group_view, name='create_group'),
    path('superadmin/group/<int:group_id>/edit/', views.edit_group_view, name='edit_group'),

    path('open-access/admin/', views.open_access_admin_view, name='open_access_admin'),
    path('open-access/admin/course/<int:course_id>/', views.open_access_course_lessons_view, name='open_access_course_lessons'),
    path('open-access/admin/course/<int:course_id>/lesson/create/', views.create_open_lesson_view, name='create_open_lesson'),
    path('open-access/panel/', views.open_access_dashboard_view, name='open_access_dashboard'),

    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/group/<int:group_id>/', views.group_detail_view, name='group_detail'),
    path(
        'admin-panel/group/<int:group_id>/remove/<int:membership_id>/',
        views.remove_student_from_group_view,
        name='remove_student_from_group',
    ),
    path(
        'admin-panel/group/<int:group_id>/exam/create/',
        views.create_control_exam_view,
        name='create_control_exam',
    ),
    path('admin-panel/exam/<int:exam_id>/grade/', views.grade_control_exam_view, name='grade_control_exam'),
    path('admin-panel/group/<int:group_id>/certificate/', views.issue_certificate_view, name='issue_certificate'),
    path('admin-panel/monitoring/', views.monitoring_view, name='monitoring'),
    path('admin-panel/monitoring/<int:group_id>/', views.monitoring_group_detail_view, name='monitoring_group_detail'),

    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/group/<int:group_id>/lesson/create/', views.create_lesson_view, name='create_lesson'),
    path('teacher/lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('teacher/lesson/<int:lesson_id>/edit/', views.edit_lesson_view, name='edit_lesson'),
    path('teacher/lesson/<int:lesson_id>/video/', views.edit_video_view, name='edit_video'),
    path('teacher/lesson/<int:lesson_id>/task/<str:level>/', views.edit_task_level_view, name='edit_task_level'),
    path('teacher/lesson/<int:lesson_id>/questions/', views.manage_questions_view, name='manage_questions'),
    path(
        'teacher/lesson/<int:lesson_id>/questions/<int:question_id>/delete/',
        views.delete_question_view,
        name='delete_question',
    ),
    path('teacher/lesson/<int:lesson_id>/quiz/', views.manage_quiz_view, name='manage_quiz'),
    path(
        'teacher/lesson/<int:lesson_id>/quiz/<int:question_id>/delete/',
        views.delete_quiz_question_view,
        name='delete_quiz_question',
    ),
    path('teacher/lesson/<int:lesson_id>/grade/', views.grade_homework_list_view, name='grade_homework_list'),
    path(
        'teacher/lesson/<int:lesson_id>/grade/<int:student_id>/',
        views.grade_student_homework_view,
        name='grade_student_homework',
    ),

    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/group/<int:group_id>/', views.student_group_lessons_view, name='student_group_lessons'),
    path(
        'student/group/<int:group_id>/exam/<int:exam_id>/submit/',
        views.submit_control_exam_view,
        name='submit_control_exam',
    ),
    path('student/group/<int:group_id>/rating/', views.student_rating_view, name='student_rating'),
    path('student/lesson/<int:lesson_id>/', views.student_lesson_view, name='student_lesson'),
    path('student/lesson/<int:lesson_id>/video/watched/', views.mark_video_watched_view, name='mark_video_watched'),
    path('student/lesson/<int:lesson_id>/task/<str:level>/unlock/', views.unlock_task_view, name='unlock_task'),
    path('student/lesson/<int:lesson_id>/task/<str:level>/submit/', views.submit_task_view, name='submit_task'),
    path('student/lesson/<int:lesson_id>/questions/submit/', views.submit_questions_view, name='submit_questions'),
    path('student/lesson/<int:lesson_id>/quiz/submit/', views.submit_quiz_view, name='submit_quiz'),
    path('student/grades/', views.student_grades_view, name='student_grades'),
    path('student/certificates/', views.student_certificates_view, name='student_certificates'),
    path('student/certificates/<int:certificate_id>/', views.certificate_detail_view, name='certificate_detail'),

    path('observer/', views.observer_dashboard_view, name='observer_dashboard'),
    path('observer/group/<int:group_id>/rating/', views.observer_rating_view, name='observer_rating'),
    path('observer/confirm/', views.confirm_review_view, name='confirm_review'),
]
