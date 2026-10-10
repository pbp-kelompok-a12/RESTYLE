from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from closet.forms import ItemForm
from closet.models import Item

@login_required(login_url="/login")
def show_closet(request):
    items = Item.objects.filter(user=request.user)
    context = {
        "items": items,
        "total_count": items.count(),
    }
    return render(request, "closet.html", context)

def option_context():
    return {
        "category_options": Item.CATEGORY_CHOICES,
        "color_options": [
            {"value": value, "label": label, "hex": Item.COLOR_HEX[value]}
            for value, label in Item.COLOR_CHOICES
        ],
        "status_options": Item.STATUS_CHOICES,
    }

@login_required(login_url="/login")
def add_item(request):
    form = ItemForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user
        item.save()
        messages.success(request, f'Yay! "{item.name}" is now in your closet!')
        return redirect("closet:show_closet")
    return render(request, "item_form.html", {"form": form, "is_edit": False, **option_context()})