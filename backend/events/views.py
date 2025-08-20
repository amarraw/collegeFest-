from django.shortcuts import render, redirect
from .models import Event, Participant
import random
from django.core.mail import send_mail
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from rest_framework import status
# Home page - Event List
def home(request):
    events = Event.objects.all()
    return render(request, "events/home.html", {"events": events})

# Event detail + registration form
def register(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        otp_code = str(random.randint(100000, 999999))
        participant = Participant.objects.create(
            name=name,
            email=email,
            phone=phone,
            event=event,
            otp_code=otp_code
        )
        # Send OTP email
        send_mail(
            subject="Your OTP for College Fest",
            message=f"Hello {name}, your OTP is {otp_code}",
            from_email="your_email@gmail.com",
            recipient_list=[email],
            fail_silently=False
        )
        return redirect('verify_otp', participant_id=participant.id)
    return render(request, "events/register.html", {"event": event})

def verify_otp(request, participant_id):
    participant = Participant.objects.get(id=participant_id)
    if request.method == "POST":
        otp_entered = request.POST['otp']
        if otp_entered == participant.otp_code:
            participant.otp_verified = True

            # Generate QR code
            qr_data = f"{participant.id}-{participant.name}-{participant.event.id}"
            qr_img = qrcode.make(qr_data)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            participant.qr_code.save(f"participant_{participant.id}.png", ContentFile(buffer.getvalue()))
            
            participant.save()

            # Send QR via email
            from django.core.mail import EmailMessage
            email = EmailMessage(
                subject="Your QR Code for College Fest",
                body=f"Hello {participant.name},\n\nYour registration is successful. Find your QR code attached.",
                from_email="your_email@gmail.com",
                to=[participant.email]
            )
            buffer.seek(0)
            email.attach(f"QR_{participant.id}.png", buffer.getvalue(), 'image/png')
            email.send(fail_silently=False)

            return redirect('dashboard', participant_id=participant.id)
        else:
            return render(request, "events/verify_otp.html", {"participant": participant, "error": "Invalid OTP"})
    return render(request, "events/verify_otp.html", {"participant": participant})

# Registration success + QR page
def success(request, participant_id):
    participant = Participant.objects.get(id=participant_id)
    return render(request, "events/success.html", {"participant": participant})


def dashboard(request, participant_id):
    participant = Participant.objects.get(id=participant_id)
    # Get all events for this participant (or just the one registered)
    events = [participant.event]  # list with single event for demo

    return render(request, "events/dashboard.html", {
        "participant": participant,
        "events": events
    })


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event, Participant
from .serializers import EventSerializer, ParticipantSerializer

@api_view(['GET'])
def home_api(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def register_api(request, event_id):
    data = request.data
    email = data.get('email')
    name = data.get('name')
    phone = data.get('phone', '')

    # Check if participant already exists for this event
    existing_participant = Participant.objects.filter(event_id=event_id, email=email).first()
    if existing_participant:
        return Response({
            "message": "Already registered",
            "id": existing_participant.id
        }, status=200)

    # Create new participant
    participant = Participant.objects.create(
        name=name,
        email=email,
        phone=phone,
        event_id=event_id
    )
    serializer = ParticipantSerializer(participant)
    return Response(serializer.data)

@api_view(['POST'])
def verify_otp_api(request, participant_id):
    data = request.data
    participant = Participant.objects.get(id=participant_id)
    if data.get('otp') == participant.otp:
        participant.verified = True
        participant.save()
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)
    return Response({'error': 'Invalid OTP'}, status=400)

@api_view(['GET'])
def dashboard_api(request, participant_id):
    print("Requested participant_id:", participant_id)
    participant = Participant.objects.get(id=participant_id)
    serializer = ParticipantSerializer(participant)
    return Response(serializer.data)
