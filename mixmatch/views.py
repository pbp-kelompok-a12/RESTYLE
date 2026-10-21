from django.contrib.auth.decorators import login_required
from django.shortcuts import render

LOGIN_URL = "/login"


@login_required(login_url=LOGIN_URL)
def show_mixmatch(request):
    return render(request, "mixmatch/mixmatch.html")