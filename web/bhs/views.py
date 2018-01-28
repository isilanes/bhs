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

    if request.method == "POST":
        form = AmountForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Create TimeInstant entry:
            ti = TimeInstant()
            ti.timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d")
            ti.timestamp = ti.timestamp.replace(hour=12)
            ti.save()

            # Create Amount entries:
            for field, value in data.items():
                if field == "timestamp":
                    continue

                amount = Amount()
                amount.value = value
                amount.account = Account.objects.get(name=field)
                amount.when = ti
                amount.save()

        # Back to stats_vs_time:
        return redirect("bhs:index")

    else:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        initial = {
            "timestamp": timestamp,
        }
        for account in Account.objects.all():
            initial[account.name] = 0.0

        context = {
            #"form": AmountForm(initial=initial),
            #"account_list": [a for a in Account.objects.all()],
        }

        return render(request, 'bhs/index.html', context)

