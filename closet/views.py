from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

from closet.forms import ItemForm
from closet.models import Item, release_finished_washes

@login_required(login_url="/login")
def show_closet(request):
    release_finished_washes(request.user)
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

@login_required(login_url="/login")
def show_item_detail(request, item_id):
    release_finished_washes(request.user)
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    return render(request, "item_detail.html", {"item": item})

@login_required(login_url="/login")
def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'"{item.name}" was updated!')
        return redirect("closet:show_item_detail", item_id=item.id)
    return render(request, "item_form.html", {"form": form, "item": item, "is_edit": True, **option_context()})


@login_required(login_url="/login")
@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    name = item.name
    item.delete()
    messages.success(request, f'"{name}" was removed from your closet.')
    return redirect("closet:show_closet")

def safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return fallback

@login_required(login_url="/login")
@require_POST
def toggle_item_status(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    if item.status == "ready":
        try:
            days = int(request.POST.get("days", 3))
        except ValueError:
            days = 3
        days = min(max(days, 1), 30)
        item.start_washing(days)
        messages.success(request, f'"{item.name}" is in the wash. Ready in {days} day{"s" if days != 1 else ""}.')
    else:
        item.mark_ready()
        messages.success(request, f'"{item.name}" is ready to wear.')
    return redirect(safe_next(request, "closet:show_closet"))