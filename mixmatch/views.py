from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_POST

from closet.models import Item, STYLE_OPTIONS
from mixmatch.forms import OutfitForm
from mixmatch.models import Outfit, SLOTS, SLOT_CATEGORIES, SLOT_LABELS, slot_for_category
from community.models import Post
from community.views import MAX_TAGS

LOGIN_URL = "/login"

def builder_context(request, form=None, outfit=None):
    items = list(Item.objects.filter(user=request.user))
    for item in items:
        item.slot = slot_for_category(item.category)

    by_id = {str(item.id): item for item in items}
    slots = []
    for key in SLOTS:
        if key == "accessories":
            if form is not None and form.is_bound:
                picked = [
                    by_id[item_id]
                    for item_id in form.data.getlist(key)
                    if item_id in by_id
                ]
            elif outfit is not None:
                picked = list(outfit.accessories.all())
            else:
                picked = []
        else:
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
        name = form.data.get("name", "")
        notes = form.data.get("notes", "")

    elif outfit is not None:
        selected_tags = outfit.tags
        name = outfit.name
        notes = outfit.notes

    else:
        selected_tags = []
        name = ""
        notes = ""

    saved_outfits = (
        Outfit.objects
        .filter(user=request.user)
        .select_related(
            "top",
            "bottom",
            "shoes",
            "outerwear",
            "dresses",
        )
        .prefetch_related("accessories")
    )

    return {
        "items": items,
        "slots": slots,
        "category_options": Item.CATEGORY_CHOICES,
        "tag_options": STYLE_OPTIONS,
        "selected_tags": selected_tags,
        "outfit": outfit,
        "name_value": name,
        "notes_value": notes,
        "saved_outfits": saved_outfits,
        "planner_return": (
            request.GET.get("planner_return")
            or request.POST.get("planner_return", "")
        ),
    }

@login_required(login_url=LOGIN_URL)
def show_mixmatch(request):
    return render(request, "mixmatch/mixmatch.html", builder_context(request))

def share_to_community(request, outfit):
    parts = [f"My outfit: {outfit.name}"]
    if outfit.notes:
        parts.append(outfit.notes)
    if outfit.tags:
        parts.append(" ".join(f"#{tag.lower()}" for tag in outfit.tags))
    post = Post.objects.create(author=request.user, content="\n\n".join(parts)[:1000])
    post.tagged_items.set(outfit.pieces[:MAX_TAGS])
    messages.success(request, f'"{outfit.name}" is now live in the community.')
    return redirect("community:show_community")

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
        form.save_m2m()
        if request.POST.get("share") == "1":
            return share_to_community(request, outfit)
        messages.success(request, f'Yay! "{outfit.name}" is saved.')
        planner_return = request.POST.get("planner_return")
        if planner_return:
            return redirect(f"{reverse('planner:show_planner')}?{urlencode({'choose_date': planner_return, 'planner_saved': '1'})}")
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
            if request.POST.get("share") == "1":
                return share_to_community(request, outfit)
            messages.success(request, f'"{outfit.name}" was updated!')
            planner_return = request.POST.get("planner_return")
            if planner_return:
                return redirect(f"{reverse('planner:show_planner')}?{urlencode({'choose_date': planner_return, 'planner_saved': '1'})}")
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
