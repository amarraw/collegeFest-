import qrcode
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Participant
from django.core.files import File
from io import BytesIO

@receiver(post_save, sender=Participant)
def generate_qr(sender, instance, created, **kwargs):
    if created and instance.otp_verified:
        qr_data = f"{instance.id}-{instance.name}-{instance.event.id}"
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer, 'PNG')
        filename = f"participant_{instance.id}.png"
        instance.qr_code.save(filename, File(buffer), save=False)
        instance.save()
