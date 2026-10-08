from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from types import SimpleNamespace

# Create your views here.
def show_landing_page(request):
    dummy_features = [
        SimpleNamespace(title="Wrap Skirt", desc="Bottom · Blue · Worn 4 times", image = "/static/img/skirt.png", status="ready"),
        SimpleNamespace(title="Floral Midi Dress", desc="Dress · Cream · Worn 2 times", image = "/static/img/midi_dress.png", status="not_ready"),
        SimpleNamespace(title="Wrap Jeans", desc="Bottom · Denim · Worn 6 times", image = "/static/img/wrap_jeans.png", status="ready"),
        SimpleNamespace(title="Layered Sweater", desc="Top · Navy · Worn 1 time", image = "/static/img/layered_sweater.png", status="ready"),
    ]
    context = {
        "dummy_features":dummy_features
    }
    return render(request, 'index.html', context)

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('main:login')

    context = {'form': form}
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main:show_main')  # Halaman utama/dashboard setelah login
        else:
            messages.error(request, 'Username atau password salah!')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    messages.success(request, 'Kamu berhasil logout.')
    return redirect('main:login')

@login_required(login_url='/login')
def show_main(request):
    context = {
        'username': request.user.username,
        # Nanti di sini ditaruh data wishlist / pengingat conscious shopping
    }
    return render(request, 'main.html', context)