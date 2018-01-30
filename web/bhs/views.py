# Standard libs:
from datetime import datetime

# Django libs:
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Our libs:
from bhs.models import  BOINCProject

# Index views:
def index(request):
    """Show index."""

    timestamp = datetime.now().strftime("%Y-%m-%d")

    context = {
        "project_list": [p for p in BOINCProject.objects.filter(active=True)],
    }

    return render(request, 'bhs/index.html', context)

def project(request, name):

    context = {
        "project": name,
    }

    return render(request, 'bhs/project.html', context)


# Data URLs:
def data_to_plot(project):
    """Return dictionary with data to plot."""

    data_dict = [
        {"x": 0, "y": 0},
    ]

    return data_dict

def project_data(request, project):
    """Return JSON data."""

    data = {
        "data": data_to_plot(project),
        "color": "#00ff00",
        "label": project,
    }

    return JsonResponse(data)

