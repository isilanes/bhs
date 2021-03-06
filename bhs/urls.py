# Django libs:
from django.urls import path

# Our web libs:
from bhs import views

# Constants:
app_name = "bhs"

# URL definitions:
urlpatterns = [
    # Index:
    path('', views.index, name='index'),

    # Single project:
    path('project/<slug:pname>/', views.project, name='project'),

    # Data URLs:
    path('project_data/<slug:pname>/<slug:what>', views.project_data, name='project_data'),

    # Action URLs:
    path('process_oldest/', views.process_oldest, name='process_oldest'),
]
