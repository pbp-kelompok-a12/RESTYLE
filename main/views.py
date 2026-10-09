from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from types import SimpleNamespace
from .models import UserProfile

def show_landing_page(request):
    dummy_features = [
        SimpleNamespace(title="Wrap Skirt", desc="Bottom · Blue · Worn 4 times", image="/static/img/skirt.png", status="ready"),
        SimpleNamespace(title="Floral Midi Dress", desc="Dress · Cream · Worn 2 times", image="/static/img/midi_dress.png", status="not_ready"),
        SimpleNamespace(title="Wrap Jeans", desc="Bottom · Denim · Worn 6 times", image="/static/img/wrap_jeans.png", status="ready"),
        SimpleNamespace(title="Layered Sweater", desc="Top · Navy · Worn 1 time", image="/static/img/layered_sweater.png", status="ready"),
    ]
    context = {
        "dummy_features": dummy_features
    }
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

    return render(request, 'style_quiz.html', {'quiz_data': quiz_data})

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # jika user baru aja ngisi kuis, simpan data ke UserProfile
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
            return redirect('main:profile') # redirect ke profile setelah login
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
