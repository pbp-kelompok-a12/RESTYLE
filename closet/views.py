from django.shortcuts import render

def show_closet(request):
    return render(request, "closet.html")