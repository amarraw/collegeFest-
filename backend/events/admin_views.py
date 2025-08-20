from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AdminUser, Participant

# ----------------------
# Admin Login View
# ----------------------
def admin_login_view(request):
    """Handle admin login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        
        if user:
            print("hello")
            print(user)
            try:
                admin_user = AdminUser.objects.get(user=user)
                print("hi")
                if admin_user.is_college_admin:
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'You are not authorized as a college admin.')
            except AdminUser.DoesNotExist:
                messages.error(request, 'You are not authorized as a college admin.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'admin/admin_login.html')

# ----------------------
# Admin Dashboard View
# ----------------------
@login_required
def admin_dashboard_view(request):
    """Show dashboard with participants"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
        if not admin_user.is_college_admin:
            messages.error(request, 'Not authorized')
            return redirect('admin_login')
    except AdminUser.DoesNotExist:
        messages.error(request, 'Not authorized')
        return redirect('admin_login')

    participants = Participant.objects.all()
    
    # Optional: Add stats
    total_participants = participants.count()
    checked_in_count = participants.filter(checked_in=True).count()
    otp_verified_count = participants.filter(otp_verified=True).count()

    context = {
        'participants': participants,
        'total_participants': total_participants,
        'checked_in_count': checked_in_count,
        'otp_verified_count': otp_verified_count,
    }
    return render(request, 'admin/admin_dashboard.html', context)

# ----------------------
# Verify Participant
# ----------------------
@login_required
def verify_participant(request, participant_id):
    """Mark a participant as checked-in"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
        if not admin_user.is_college_admin:
            messages.error(request, 'Not authorized')
            return redirect('admin_dashboard')
    except AdminUser.DoesNotExist:
        messages.error(request, 'Not authorized')
        return redirect('admin_dashboard')

    participant = Participant.objects.get(id=participant_id)
    participant.checked_in = True
    participant.save()
    messages.success(request, f'{participant.name} verified successfully')
    return redirect('admin_dashboard')
