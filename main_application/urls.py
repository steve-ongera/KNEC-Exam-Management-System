from django.urls import path
from . import views


urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/knec/', views.knec_dashboard, name='knec_dashboard'),
    path('dashboard/marks-entry/', views.marks_entry_dashboard, name='marks_entry_dashboard'),
    path('dashboard/school-admin/', views.school_admin_dashboard, name='school_admin_dashboard'),
    path('dashboard/school-staff/', views.school_staff_dashboard, name='school_staff_dashboard'),
]