from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from closet.forms import ItemForm
from closet.models import Item, SEASON_OPTIONS, STYLE_OPTIONS, WEATHER_OPTIONS

def wants_modal(request):
    return request.GET.get("modal") == "1" or request.headers.get("x-requested-with") == "fetch"

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
    "style_options": STYLE_OPTIONS,
    "season_options": SEASON_OPTIONS,
    "weather_options": WEATHER_OPTIONS,
    }

@login_required(login_url="/login")
def add_item(request):
    form = ItemForm(request.POST or None, request.FILES or None)
    modal = wants_modal(request)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user
        item.save()
        messages.success(request, f'Yay! "{item.name}" is now in your closet!')
        if modal:
            return JsonResponse({"ok": True})
        return redirect("closet:show_closet")
    ctx = {"form": form, "is_edit": False, "is_modal": modal, **option_context()}
    status = 400 if modal and request.method == "POST" else 200
    return render(request, "_item_form.html" if modal else "item_form.html", ctx, status=status)

@login_required(login_url="/login")
def show_item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    modal = wants_modal(request)
    return render(request, "_item_detail.html" if modal else "item_detail.html", {"item": item})

@login_required(login_url="/login")
def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)
    modal = wants_modal(request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'"{item.name}" was updated!')
        if modal:
            return JsonResponse({"ok": True})
        return redirect("closet:show_item_detail", item_id=item.id)
    ctx = {"form": form, "item": item, "is_edit": True, "is_modal": modal, **option_context()}
    status = 400 if modal and request.method == "POST" else 200
    return render(request, "_item_form.html" if modal else "item_form.html", ctx, status=status)

@login_required(login_url="/login")
@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id, user=request.user)
    name = item.name
    item.delete()
    messages.success(request, f'"{name}" was removed from your closet.')
    if wants_modal(request):
        return JsonResponse({"ok": True})
    return redirect("closet:show_closet")