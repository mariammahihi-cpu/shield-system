from django.shortcuts import render
from .models import MechanicalFault

def fault_list(request):
    faults = MechanicalFault.objects.all()
    return render(request, 'faults/fault_list.html', {'faults': faults})