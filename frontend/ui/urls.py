from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    
    path("rooms/", views.rooms_page, name="rooms"),
    path("rooms-admin/", views.rooms_admin_page, name="rooms_admin"),
    path("rooms-eq-admin/", views.rooms_eq_admin_page, name="rooms_eq_admin"),
    path("equipments-manage/", views.equipments_manage_page, name="equipments"),
    path("rooms-search/", views.rooms_search_page, name="rooms_search"),
    
    path("reservations-list/", views.reservations_list_page, name="reservations_list"),
    path("my-reservations/", views.my_reservations_page, name="my_reservations"),
    path("all-reservations/", views.all_reservations_page, name="all_reservations"),
    
    
    path("register/", views.register_page, name="register"),
    path("reserve/", views.reserve_page, name="reserve"),
    path("reports/", views.reports_page, name="reports"),
    
    path("system-health/", views.system_health_page, name="system_health"),
]