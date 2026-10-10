from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from closet.models import Item

@login_required(login_url="/login")
def show_closet(request):
    items = Item.objects.filter(user=request.user)
    context = {
        "items": items,
        "total_count": items.count(),
    }
    return render(request, "closet.html", context)