from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('edit/', views.editor_view, name='editor'),
    path('file-operations/', views.file_operations, name='file_operations'),
]