from django.db import models
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import os

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=200)
    date = models.DateTimeField()
    max_participants = models.IntegerField(default=100)
    
    def __str__(self):
        return self.name

class Participant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    checked_in = models.BooleanField(default=False)

    class Meta:
        pass
    
    def __str__(self):
        return f"{self.name} - {self.event.name}"
    
    def save(self, *args, **kwargs):
        if not self.qr_code and self.id:
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(self.id))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        filename = f'participant_{self.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_college_admin = models.BooleanField(default=False)
    can_scan_qr = models.BooleanField(default=True)
    can_manage_participants = models.BooleanField(default=True)
    can_manage_events = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Admin: {self.user.username}"
    
    @property
    def username(self):
        return self.user.username
    
    @property
    def email(self):
        return self.user.email
