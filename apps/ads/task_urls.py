# Layer: api
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ads.views.task_view import TaskViewSet

router = DefaultRouter()
router.register("", TaskViewSet, basename="task")

app_name = "tasks"

urlpatterns = [path("", include(router.urls))]
