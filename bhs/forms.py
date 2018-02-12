# Django libs:
from django import forms

# Our libs:
from ahorro.models import Account

# Classes:
class AmountForm(forms.Form):
    timestamp = forms.CharField(label="Date", max_length=10)
    #total_kms = forms.IntegerField(label="Total kms")
    #partial_kms = forms.FloatField(label="Partial kms")

    def __init__(self, *args, **kwargs):
        super(AmountForm, self).__init__(*args, **kwargs)

        for account in Account.objects.all():
            self.fields[account.name] = forms.FloatField(label=account.name)

