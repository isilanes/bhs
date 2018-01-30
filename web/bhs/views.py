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
    initial = {
        "timestamp": timestamp,
    }

    context = {
        #"form": AmountForm(initial=initial),
        #"account_list": [a for a in Account.objects.all()],
    }

    return render(request, 'bhs/index.html', context)

