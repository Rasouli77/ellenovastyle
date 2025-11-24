from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from .models import MyUser
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from .form import EditUser, Register
from . import helper
from django.contrib import messages

# Create your views here.

def mobile_login(request):
    if request.method == 'POST':
        if 'mobile' in request.POST:
            mobile = request.POST.get('mobile')
            user = MyUser.objects.get(mobile=mobile)
            login(request, user)
            return HttpResponseRedirect(reverse('dashboard'))

    return render(request, 'mobile_login.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def edit_user(request, user_id):
    user = get_object_or_404(MyUser, id=user_id)
    if request.method == "POST":
        form = EditUser(request.POST, instance=user)
        if form.is_valid():
            form.save()
            next_url = request.GET.get("next") or request.POST.get("next") or "/"
            return redirect(next_url)
        
    else:
        form = EditUser(instance=user)
    if request.user.id != user.id:
        return HttpResponseForbidden("فاقد اجازه دسترسی")
    return render(request, "edit_user.html", { "form": form })

def register(request):
    form = Register
    messages.error(request, "")
    if request.method == 'POST':
        try:
            if "mobile" in request.POST:
                mobile = request.POST.get("mobile")
                user = MyUser.objects.get(mobile=mobile)
                # send otp
                otp = helper.get_random_otp()
                helper.send_otp(mobile, otp)
                # save otp
                print(otp)
                user.otp = otp
                user.save()
                request.session['user_mobile'] = user.mobile
                return redirect(reverse('account-verify'))

        except MyUser.DoesNotExist:
            form = Register(request.POST)
            if form.is_valid():
                print('valid')
                user = form.save(commit=False)
                # Set the username to the mobile number
                user.username = mobile
                # send otp
                otp = helper.get_random_otp()
                helper.send_otp(mobile, otp)
                # save otp
                print(otp)
                user.otp = otp
                user.is_active = False
                user.save()
                request.session['user_mobile'] = user.mobile
                return redirect(reverse('account-verify'))

    return render(request, 'register.html', {"form": form})

def verify(request):
    try:
        mobile = request.session.get('user_mobile')
        user = MyUser.objects.get(mobile=mobile)
        if request.method == 'POST':


            # check otp expiration
            if not helper.check_otp_expiration(user.mobile):
                messages.error(request, "کد ارسالی منقضی شده، لطفا دوباره تلاش کنید.")
                return redirect(reverse('register'))
            
            if user.otp != int(request.POST.get('otp')):
                messages.error(request, "کد وارد شده اشتباه است.")
                return redirect(reverse('register'))
            
            else:

                user.is_active = True
                user.set_password(mobile)
                user.save()
                login(request, user)
                messages.success(request, "ورود موفق.")
                return redirect(reverse('index'))

        return render(request, 'account-verify.html', {'mobile': mobile})
    except MyUser.DoesNotExist:
        return redirect(reverse('register'))
    