from django.urls import path
from app import views


urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('action/logout', views.logout, name='logout'),
    path('redirect', views.redirect_url, name='redirect'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('data/chat_log', views.get_chat_log, name='chat_log'),
    path('data/questions', views.get_questions, name='questions'),
    path('data/answers', views.get_answers, name='answers'),
    path('data/commands', views.get_commands, name='commands'),
    path('data/responses', views.get_responses, name='responses'),
    path('data/aliases', views.get_aliases, name='aliases'),
    path('denied', views.denied, name='denied'),
]