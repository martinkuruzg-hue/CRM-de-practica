from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'logs', views.InteractionLogViewSet)
router.register(r'system-prompts', views.SystemPromptViewSet)
router.register(r'evaluations', views.ResponseEvaluationViewSet)

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('', include(router.urls)),
]
