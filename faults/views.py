from django.shortcuts import render
from .models import MechanicalFault
from django.contrib.auth.decorators import login_required

@login_required
def fault_list(request):
    faults = (
        MechanicalFault.objects
        .select_related('reported_by', 'trip', 'station', 'truck')
        .order_by('-created_at')
    )
    return render(request, 'faults/fault_list.html', {'faults': faults})