from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from closet.forms import ItemForm
from django.db.models import Q
from closet.models import (
    ALL_YEAR,
    MANUAL_STATUS_CATEGORIES,
    SEASON_OPTIONS,
    STYLE_OPTIONS,
    WEATHER_OPTIONS,
    Item,
)
from planner.services import sync_item_statuses

FILTER_KEYS = ("cat", "color", "style", "season", "weather", "status", "q")

def chip_url(request, **changes):
    params = request.GET.copy()
    for key, value in changes.items():
        if value:
            params[key] = value
        else:
            params.pop(key, None)
    query = params.urlencode()
    return f"?{query}" if query else "?"

def wants_modal(request):
    return request.GET.get("modal") == "1" or request.headers.get("x-requested-with") == "fetch"

@login_required(login_url="/login")
def show_closet(request):
    sync_item_statuses(request.user)
    filters = {key: request.GET.get(key, "").strip() for key in FILTER_KEYS}
    all_items = Item.objects.filter(user=request.user)
    items = all_items

    if filters["cat"]:
        items = items.filter(category=filters["cat"])
    if filters["color"]:
        items = items.filter(color=filters["color"])
    if filters["status"]:
        items = items.filter(status=filters["status"])
    if filters["q"]:
        items = items.filter(
            Q(name__icontains=filters["q"])
            | Q(store__icontains=filters["q"])
            | Q(material__icontains=filters["q"])
        )

    # kolom list (JSON) difilter di Python supaya jalan di SQLite dan PostgreSQL
    items = list(items)
    if filters["style"]:
        items = [i for i in items if filters["style"] in i.styles]
    if filters["season"]:
        items = [i for i in items if filters["season"] in i.seasons or ALL_YEAR in i.seasons]
    if filters["weather"]:
        items = [i for i in items if filters["weather"] in i.weather]

    cat_chips = [{"label": "All", "url": chip_url(request, cat=""), "active": not filters["cat"]}]
    for value, label in Item.CATEGORY_CHOICES:
        cat_chips.append({"label": label, "url": chip_url(request, cat=value), "active": filters["cat"] == value})

    context = {
        "items": items,
        "total_count": all_items.count(),
        "shown_count": len(items),
        "f": filters,
        "has_filters": any(filters.values()),
        "cat_chips": cat_chips,
        "status_options": Item.STATUS_CHOICES,
        **option_context(),
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
@require_POST
def change_status(request, item_id):
    item = get_object_or_404(
        Item.objects.filter(category__in=MANUAL_STATUS_CATEGORIES),
        pk=item_id,
        user=request.user,
    )
    item.change_status()
    messages.success(request, f'"{item.name}" is now {item.get_status_display().lower()}.')
    return redirect("closet:show_closet")

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
