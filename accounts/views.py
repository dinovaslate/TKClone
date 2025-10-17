from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import RegistrationForm


class AuthLoginView(LoginView):
    template_name = 'accounts/login.html'


class AuthLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


class RegisterView(View):
    form_class = RegistrationForm
    template_name = 'accounts/register.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:home')
        return render(request, self.template_name, {"form": form})
