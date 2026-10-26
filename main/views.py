import os
import requests
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from types import SimpleNamespace
from .models import PERSONAS, UserProfile, WishlistItem
from closet.models import Item as ClosetItem

COLOR_HEX_MAP = {
    "White": "#FFFFFF", "Black": "#000000", "Gray": "#808080",
    "Beige": "#F5F5DC", "Brown": "#7B3F00", "Red": "#D9381E",
    "Orange": "#FFA500", "Yellow": "#FFFF00", "Pink": "#FFC0CB",
    "Green": "#008000", "Blue": "#0000FF", "Purple": "#47005C"
}

def show_landing_page(request):
    dummy_features = [
        SimpleNamespace(title="Wrap Skirt", desc="Bottom · Blue · Worn 4 times", image="/static/img/skirt.png", status="ready"),
        SimpleNamespace(title="Floral Midi Dress", desc="Dress · Cream · Worn 2 times", image="/static/img/midi_dress.png", status="not_ready"),
        SimpleNamespace(title="Wrap Jeans", desc="Bottom · Denim · Worn 6 times", image="/static/img/wrap_jeans.png", status="ready"),
        SimpleNamespace(title="Layered Sweater", desc="Top · Navy · Worn 1 time", image="/static/img/layered_sweater.png", status="ready"),
    ]
    context = {"dummy_features": dummy_features}
    return render(request, 'index.html', context)

def style_quiz(request):
    if request.method == "POST":
        quiz_data = {
            'preferred_style': request.POST.get('style_persona'),
            'conscious_priority': request.POST.get('conscious_priority'),
            'wardrobe_goal': request.POST.get('wardrobe_goal')
        }

        if request.user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'style_persona': 'The Conscious Minimalist'}
            )
            profile.preferred_style = quiz_data['preferred_style'] or ''
            profile.conscious_shopping_priority = quiz_data['conscious_priority'] or ''
            profile.wardrobe_goal = quiz_data['wardrobe_goal'] or ''
            profile.style_persona = quiz_data['preferred_style'] or 'The Conscious Minimalist'
            profile.save()
            return redirect('main:profile')

        request.session['quiz_data'] = quiz_data
        return redirect('main:register')

    quiz_data = {}
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = None

        if profile:
            quiz_data = {
                'preferred_style': profile.preferred_style,
                'conscious_priority': profile.conscious_shopping_priority,
                'wardrobe_goal': profile.wardrobe_goal,
            }

    personas = {
        key: {"title": title, "description": description, "icon": icon}
        for key, (title, description, icon) in PERSONAS.items()
    }
    return render(request, 'style_quiz.html', {'quiz_data': quiz_data, 'personas': personas})

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            quiz_data = request.session.get('quiz_data', {})
            UserProfile.objects.create(
                user=user,
                preferred_style=quiz_data.get('preferred_style') or '',
                conscious_shopping_priority=quiz_data.get('conscious_priority') or '',
                wardrobe_goal=quiz_data.get('wardrobe_goal') or '',
                style_persona=quiz_data.get('preferred_style') or 'The Conscious Minimalist'
            )
            if 'quiz_data' in request.session:
                del request.session['quiz_data']

            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('main:login')

    context = {'form': form}
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main:profile')
        else:
            messages.error(request, 'Invalid username or password!')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('main:login')

@login_required(login_url='/login')
def profile_view(request):
    return redirect('community:show_user_profile', username=request.user.username)


# --- WISHLIST & CONSCIOUS SHOPPING LOGIC ---

@login_required
def wishlist_view(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user).order_by('-id')
    closet_items = ClosetItem.objects.filter(user=request.user)
    closet_set = set((item.category.lower(), item.color.lower()) for item in closet_items)
    
    closest_matches_count = 0

    for item in wishlist_items:
        item.color_hex = COLOR_HEX_MAP.get(item.color.capitalize(), "#3F6699")
        if (item.category.lower(), item.color.lower()) in closet_set:
            item.has_match = True
            closest_matches_count += 1
        else:
            item.has_match = False

    is_conscious_shopping = closest_matches_count > 0

    context = {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_items.count(),
        'closest_matches_count': closest_matches_count,
        'is_conscious_shopping': is_conscious_shopping,
    }
    return render(request, "wishlist.html", context)


@login_required
def add_wishlist_item(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        color = request.POST.get("color")
        material = request.POST.get("material", "")
        brand = request.POST.get("brand", "")
        link = request.POST.get("link", "")
        price = request.POST.get("price") or 0
        photo = request.FILES.get("photo")
        photo_url = request.POST.get("photo_url")

        style_tags = request.POST.getlist("style_tags")
        style_tag = style_tags[0] if style_tags else ""

        wishlist_item = WishlistItem(
            user=request.user,
            name=name,
            category=category,
            color=color,
            material=material,
            brand=brand,
            link=link,
            price=price,
            style_tag=style_tag
        )

        if photo:
            wishlist_item.photo = photo
        elif photo_url and photo_url.startswith(("http://", "https://", "/media/")):
            try:
                if photo_url.startswith("/media/"):
                    photo_url = request.build_absolute_uri(photo_url)
                
                resp = requests.get(photo_url, timeout=5)
                if resp.status_code == 200:
                    filename = os.path.basename(photo_url.split("?")[0]) or f"community_{request.user.id}.jpg"
                    wishlist_item.photo.save(filename, ContentFile(resp.content), save=False)
            except Exception as e:
                print("Error downloading community photo:", e)

        wishlist_item.save()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "success"}, status=200)

        return redirect("main:wishlist")


@login_required
@require_POST
def toggle_wishlist_from_community(request):
    name = request.POST.get("name")
    category = request.POST.get("category", "Top")
    color = request.POST.get("color", "White")
    material = request.POST.get("material", "")
    brand = request.POST.get("brand", "")
    link = request.POST.get("link", "")
    price = request.POST.get("price") or 0
    photo_url = request.POST.get("photo_url", "")

    # Cek apakah item sudah ada di wishlist pengguna
    existing_item = WishlistItem.objects.filter(user=request.user, name=name).first()

    if existing_item:
        # Hapus jika sudah ada (Remove)
        existing_item.delete()
        return JsonResponse({"status": "removed", "saved": False})

    # Tambahkan jika belum ada (Add)
    wishlist_item = WishlistItem(
        user=request.user,
        name=name,
        category=category,
        color=color,
        material=material,
        brand=brand,
        link=link,
        price=price,
        style_tag=""
    )

    # Unduh dan simpan gambar jika photo_url tersedia
    if photo_url and photo_url.startswith(("http://", "https://", "/media/")):
        try:
            if photo_url.startswith("/media/"):
                photo_url = request.build_absolute_uri(photo_url)
            
            resp = requests.get(photo_url, timeout=5)
            if resp.status_code == 200:
                filename = os.path.basename(photo_url.split("?")[0]) or f"community_{request.user.id}.jpg"
                wishlist_item.photo.save(filename, ContentFile(resp.content), save=False)
        except Exception as e:
            print("Error downloading community photo:", e)

    wishlist_item.save()

    return JsonResponse({"status": "added", "saved": True})


@login_required
def get_wishlist_detail(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    
    # Cari item di Digital Closet yang memiliki category & color yang sama
    matching_closet_items = ClosetItem.objects.filter(
        user=request.user,
        category__iexact=item.category,
        color__iexact=item.color
    )
    
    matched_items_data = []
    for closet_item in matching_closet_items:
        matched_items_data.append({
            "name": closet_item.name,
            "photo_url": closet_item.photo.url if closet_item.photo else "/static/img/bunglon_hires.png"
        })

    data = {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "color": item.color,
        "color_hex": COLOR_HEX_MAP.get(item.color.capitalize(), "#3F6699"),
        "material": item.material or "-",
        "brand": item.brand or "-",
        "link": item.link or "",
        "price": f"Rp {item.price:,.0f}".replace(",", ".") if item.price else "Rp 0",
        "raw_price": item.price,
        "photo_url": item.photo.url if item.photo else "",
        "style_tag": item.style_tag or "-",
        "has_match": len(matched_items_data) > 0,
        "matched_items": matched_items_data
    }
    return JsonResponse(data)


@login_required
def edit_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    if request.method == "POST":
        item.name = request.POST.get("name", item.name)
        item.category = request.POST.get("category", item.category)
        item.color = request.POST.get("color", item.color)
        item.material = request.POST.get("material", "")
        item.brand = request.POST.get("brand", "")
        item.link = request.POST.get("link", "")
        item.price = request.POST.get("price") or 0

        if request.FILES.get("photo"):
            item.photo = request.FILES.get("photo")

        style_tags = request.POST.getlist("style_tags")
        if style_tags:
            item.style_tag = style_tags[0]

        item.save()
        return JsonResponse({"status": "success"})


@login_required
@require_POST
def delete_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    item.delete()
    return JsonResponse({"status": "success"})