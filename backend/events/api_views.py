from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Event, Participant, AdminUser
from .serializers import EventSerializer, ParticipantSerializer
import json
import random
import string
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
import os

# ----- List all events -----
@api_view(['GET'])
def event_list(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

# ----- Register participant -----
@api_view(['POST'])
def register_participant(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        data = request.data
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        participant = Participant.objects.create(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),  # Make phone optional
            event=event,
            otp_code=otp_code
        )
        
        print(f"OTP for {participant.email}: {otp_code}")  # For demo
        
        # Send OTP via email
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"Your OTP for {event.name}"
            message = f"""
Hello {participant.name},

Your registration for {event.name} is successful!

Your OTP code is: {otp_code}

Please enter this OTP in the app to complete your registration.

Event Details:
- Event: {event.name}
- Venue: {event.venue}
- Date: {event.date}

Best regards,
College Fest Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[participant.email],
                fail_silently=False,
            )
            print(f"✅ OTP email sent to {participant.email}")
            
        except Exception as email_error:
            print(f"❌ Failed to send email: {email_error}")
            # Don't fail the registration if email fails
        
        # Generate QR code
        import qrcode
        from django.core.files.base import ContentFile
        from io import BytesIO
        
        qr_data = f"{participant.id}-{participant.name}-{participant.event.id}"
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        participant.qr_code.save(f"participant_{participant.id}.png", ContentFile(buffer.getvalue()))
        participant.save()
        
        serializer = ParticipantSerializer(participant)
        return Response({
            'id': participant.id,
            'name': participant.name,
            'email': participant.email,
            'message': f'Registration successful! OTP sent to {participant.email}',
            'otp_code': otp_code  # Include OTP in response for testing
        })
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ----- Verify OTP -----
@api_view(['POST'])
def verify_otp(request, participant_id):
    try:
        participant = Participant.objects.get(id=participant_id)
        otp_entered = request.data.get('otp')
        
        if otp_entered == participant.otp_code:
            participant.otp_verified = True
            participant.save()
            
            # Send QR code via email after successful OTP verification
            try:
                from django.core.mail import EmailMessage
                from django.conf import settings
                
                subject = f"🎉 Registration Complete - {participant.event.name}"
                message = f"""
Hello {participant.name},

🎊 Congratulations! Your registration for {participant.event.name} is now complete.

Your OTP has been verified successfully, and your QR code is attached to this email.

Event Details:
- Event: {participant.event.name}
- Venue: {participant.event.venue}
- Date: {participant.event.date}

📱 How to use your QR code:
1. Save the QR code image to your phone
2. Show it at the event entrance for check-in
3. Keep it handy throughout the event

Your QR code contains your unique participant ID: {participant.id}

Best regards,
College Fest Team
                """
                
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[participant.email]
                )
                
                # Attach the QR code image
                if participant.qr_code:
                    email.attach_file(participant.qr_code.path)
                    print(f"✅ QR code email sent to {participant.email}")
                else:
                    print(f"⚠️ No QR code found for participant {participant.id}")
                
                email.send(fail_silently=False)
                
            except Exception as email_error:
                print(f"❌ Failed to send QR code email: {email_error}")
                # Don't fail the OTP verification if email fails
            
            return Response({
                'status': 'verified', 
                'participant_id': participant.id,
                'message': 'OTP verified successfully! QR code sent to your email.'
            })
        else:
            return Response({'status': 'invalid', 'error': 'Invalid OTP'}, status=400)
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ----- Check Participant -----
@api_view(['GET'])
def check_participant(request):
    email = request.GET.get('email')
    event_id = request.GET.get('event_id')
    
    if not email or not event_id:
        return Response({'error': 'Email and event_id are required'}, status=400)
    
    try:
        participant = Participant.objects.get(email=email, event__id=event_id)
        return Response({
            'exists': True,
            'participant_id': participant.id,
            'name': participant.name,
            'email': participant.email
        })
    except Participant.DoesNotExist:
        return Response({'exists': False}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ----- Register Existing User -----
@api_view(['POST'])
def register_existing_user(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        email = request.data.get('email')
        name = request.data.get('name')
        phone = request.data.get('phone', '')
        
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        # Find existing participant with this email (from any event)
        try:
            existing_participant = Participant.objects.filter(email=email).first()
            if not existing_participant:
                return Response({'error': 'No existing user found with this email'}, status=404)
                
            # Check if already registered for this event
            if Participant.objects.filter(email=email, event=event).exists():
                participant = Participant.objects.get(email=email, event=event)
                return Response({
                    'id': participant.id,
                    'message': 'Already registered for this event'
                })
                
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            
            # Create new participant for this event using provided info or existing info
            participant = Participant.objects.create(
                name=name or existing_participant.name,
                email=email,
                phone=phone or existing_participant.phone,
                event=event,
                otp_code=otp_code
            )
            
            # Send OTP via email
            try:
                subject = f"Your OTP for {event.name}"
                message = f"""
Hello {participant.name},

Your registration for {event.name} is successful!

Your OTP code is: {otp_code}

Please enter this OTP in the app to complete your registration.

Event Details:
- Event: {event.name}
- Venue: {event.venue}
- Date: {event.date}

Best regards,
College Fest Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[participant.email],
                    fail_silently=False,
                )
                print(f"✅ OTP email sent to {participant.email}")
                
            except Exception as email_error:
                print(f"❌ Failed to send email: {email_error}")
            
            # Generate QR code
            import qrcode
            from django.core.files.base import ContentFile
            from io import BytesIO
            
            qr_data = f"{participant.id}-{participant.name}-{participant.event.id}"
            qr_img = qrcode.make(qr_data)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            participant.qr_code.save(f"participant_{participant.id}.png", ContentFile(buffer.getvalue()))
            participant.save()
            
            return Response({
                'id': participant.id,
                'name': participant.name,
                'email': participant.email,
                'message': f'Registration successful! OTP sent to {participant.email}',
                'otp_code': otp_code  # Include OTP in response for testing
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
            
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ----- Dashboard -----
@api_view(['GET'])
def dashboard(request, participant_id):
    try:
        participant = Participant.objects.get(id=participant_id)
        serializer = ParticipantSerializer(participant)
        data = serializer.data
        
        # Return the actual QR code URL if it exists
        if participant.qr_code:
            data['qr_code'] = request.build_absolute_uri(participant.qr_code.url)
        else:
            data['qr_code'] = None
            
        return Response(data)
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ----- Success (optional) -----
@api_view(['GET'])
def success(request, participant_id):
    return Response({'message': 'Registration successful!'})

# ----- Test OTP generation -----
@api_view(['POST'])
def test_otp(request):
    """Test endpoint to verify OTP generation and email"""
    try:
        import random
        test_otp = str(random.randint(100000, 999999))
        
        # Test email sending
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = "Test OTP Email"
        message = f"""
This is a test email to verify OTP functionality.

Test OTP: {test_otp}

If you receive this email, the email configuration is working correctly.
        """
        
        test_email = request.data.get('email', 'amar.raw011@gmail.com')
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Test OTP email sent successfully!',
            'otp': test_otp,
            'email': test_email
        })
        
    except Exception as e:
        return Response({'error': f'Test failed: {str(e)}'}, status=400)

# ----- Resend QR Code -----
@api_view(['POST'])
def resend_qr(request, participant_id):
    """Resend QR code via email"""
    try:
        participant = Participant.objects.get(id=participant_id)
        
        if not participant.otp_verified:
            return Response({'error': 'OTP must be verified first'}, status=400)
        
        # Send QR code via email
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            subject = f"📱 QR Code - {participant.event.name}"
            message = f"""
Hello {participant.name},

Here's your QR code for {participant.event.name}.

Event Details:
- Event: {participant.event.name}
- Venue: {participant.event.venue}
- Date: {participant.event.date}

📱 How to use your QR code:
1. Save the QR code image to your phone
2. Show it at the event entrance for check-in
3. Keep it handy throughout the event

Your QR code contains your unique participant ID: {participant.id}

Best regards,
College Fest Team
            """
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[participant.email]
            )
            
            # Attach the QR code image
            if participant.qr_code:
                email.attach_file(participant.qr_code.path)
                email.send(fail_silently=False)
                print(f"✅ QR code resent to {participant.email}")
                
                return Response({
                    'message': 'QR code resent successfully to your email!',
                    'email': participant.email
                })
            else:
                return Response({'error': 'QR code not found'}, status=404)
                
        except Exception as email_error:
            print(f"❌ Failed to resend QR code email: {email_error}")
            return Response({'error': 'Failed to send email'}, status=500)
            
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@csrf_exempt
def admin_login(request):
    """Admin login endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is admin
        try:
            admin_user = AdminUser.objects.get(user=user)
            if not admin_user.is_college_admin:
                return Response({
                    'success': False,
                    'message': 'User is not authorized as college admin'
                }, status=status.HTTP_403_FORBIDDEN)
        except AdminUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User is not authorized as college admin'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate or get token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'permissions': {
                    'can_scan_qr': admin_user.can_scan_qr,
                    'can_manage_participants': admin_user.can_manage_participants,
                    'can_manage_events': admin_user.can_manage_events,
                }
            }
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_participants(request):
    """Get all participants for admin dashboard"""
    try:
        # Check if user is admin
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            if not admin_user.is_college_admin:
                return Response({
                    'success': False,
                    'message': 'Not authorized'
                }, status=status.HTTP_403_FORBIDDEN)
        except AdminUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Not authorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        participants = Participant.objects.all().select_related('event')
        serializer = ParticipantSerializer(participants, many=True)
        
        return Response({
            'success': True,
            'participants': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_in_participant(request, participant_id):
    """Check in a participant by QR code"""
    try:
        # Check if user is admin
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            if not admin_user.is_college_admin or not admin_user.can_scan_qr:
                return Response({
                    'success': False,
                    'message': 'Not authorized to scan QR codes'
                }, status=status.HTTP_403_FORBIDDEN)
        except AdminUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Not authorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get participant
        try:
            participant = Participant.objects.get(id=participant_id)
        except Participant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Participant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already checked in
        if participant.checked_in:
            return Response({
                'success': False,
                'message': 'Participant already checked in',
                'participant': ParticipantSerializer(participant).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check in participant
        participant.checked_in = True
        participant.save()
        
        return Response({
            'success': True,
            'message': f'{participant.name} checked in successfully',
            'participant': ParticipantSerializer(participant).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_stats(request):
    """Get admin dashboard statistics"""
    try:
        # Check if user is admin
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            if not admin_user.is_college_admin:
                return Response({
                    'success': False,
                    'message': 'Not authorized'
                }, status=status.HTTP_403_FORBIDDEN)
        except AdminUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Not authorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        total_participants = Participant.objects.count()
        checked_in_count = Participant.objects.filter(checked_in=True).count()
        otp_verified_count = Participant.objects.filter(otp_verified=True).count()
        total_events = Event.objects.count()
        
        return Response({
            'success': True,
            'stats': {
                'total_participants': total_participants,
                'checked_in_count': checked_in_count,
                'otp_verified_count': otp_verified_count,
                'total_events': total_events,
                'check_in_rate': round((checked_in_count / total_participants * 100) if total_participants > 0 else 0, 1)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
