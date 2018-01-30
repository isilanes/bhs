# Django libs:
from django.urls import path

# Our web libs:
from bhs import views

app_name = "bhs"
# URL definitions:
urlpatterns = [
    # Index:
    path('', views.index, name='index'),

    # Single project:
    path('project/<slug:name>/', views.project, name='project'),

    # Data URLs:
    path('project_data/<slug:project>/', views.project_data, name='project_data'),
]