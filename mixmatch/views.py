from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from closet.models import Item, STYLE_OPTIONS
from mixmatch.forms import OutfitForm
from mixmatch.models import Outfit, SLOTS, SLOT_CATEGORIES, SLOT_LABELS, slot_for_category

LOGIN_URL = "/login"

def builder_context(request, form=None, outfit=None):
    items = list(Item.objects.filter(user=request.user))
    for item in items:
        item.slot = slot_for_category(item.category)

    by_id = {str(item.id): item for item in items}
    slots = []
    for key in SLOTS:
        if form is not None and form.is_bound:
            picked = by_id.get(form.data.get(key, ""))
        elif outfit is not None:
            picked = getattr(outfit, key)
        else:
            picked = None
        slots.append({
            "key": key,
            "label": SLOT_LABELS[key],
            "item": picked,
            "categories": ",".join(SLOT_CATEGORIES[key]),
        })

    if form is not None and form.is_bound:
        selected_tags = form.data.getlist("tags")
        name, notes = form.data.get("name", ""), form.data.get("notes", "")
    elif outfit is not None:
        selected_tags, name, notes = outfit.tags, outfit.name, outfit.notes
    else:
        selected_tags, name, notes = [], "", ""

    return {
        "items": items,
        "slots": slots,
        "category_options": Item.CATEGORY_CHOICES,
        "tag_options": STYLE_OPTIONS,
        "selected_tags": selected_tags,
        "outfit": outfit,
        "name_value": name,
        "notes_value": notes,
        "saved_outfits": Outfit.objects.filter(user=request.user).select_related(*SLOTS),
        "new_purchases": 0,
    }

@login_required(login_url=LOGIN_URL)
def show_mixmatch(request):
    return render(request, "mixmatch/mixmatch.html", builder_context(request))

def report_errors(request, form):
    for errors in form.errors.values():
        messages.error(request, errors[0])
        break

@login_required(login_url=LOGIN_URL)
@require_POST
def save_outfit(request):
    form = OutfitForm(request.POST, user=request.user)
    if form.is_valid():
        outfit = form.save(commit=False)
        outfit.user = request.user
        outfit.save()
        messages.success(request, f'Yay! "{outfit.name}" is saved.')
        return redirect("mixmatch:show_mixmatch")
    report_errors(request, form)
    return render(request, "mixmatch/mixmatch.html", builder_context(request, form=form), status=400)

@login_required(login_url=LOGIN_URL)
def edit_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, pk=outfit_id, user=request.user)
    form = OutfitForm(request.POST or None, instance=outfit, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f'"{outfit.name}" was updated!')
            return redirect("mixmatch:show_mixmatch")
        report_errors(request, form)
        return render(request, "mixmatch/mixmatch.html", builder_context(request, form=form, outfit=outfit), status=400)
    return render(request, "mixmatch/mixmatch.html", builder_context(request, outfit=outfit))

@login_required(login_url=LOGIN_URL)
@require_POST
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, pk=outfit_id, user=request.user)
    name = outfit.name
    outfit.delete()
    messages.success(request, f'"{name}" was removed from your saved outfits.')
    return redirect("mixmatch:show_mixmatch")