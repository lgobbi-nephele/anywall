import os

from django.db import models

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anywall.settings")
from colorfield.fields import ColorField
# from django.contrib.postgres.fields import JSONField
import uuid

VISUALIZZAZIONE = {
    'OPENGL' : 0,
    'BROWSERWINDOW': 1,
    'DESKTOP' : 2,
}

MODE = {
    'TELECAMERE' : 0, 
    'BROWSER' : 1, 
    'ALLARME' : 2, 
    'DESKTOP' : 3, 
}

IMAGE_SCOPE = {
    'NONE': 0,
    'PLACEHOLDER': 1,
    'LOGO': 2,
    'ALARM_ICON': 3,
    'WATERMARK': 4,
    }

class SignalingMessage(models.Model):
    message_type = models.CharField(max_length=10)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Window(models.Model):
    window_id = models.IntegerField(primary_key=True)
    stream = models.CharField(max_length=255, blank=True, default='')
    labelText = models.CharField(max_length=255, blank=True, default='')
    zoom = models.IntegerField(default=1)
    isZoom = models.BooleanField(default=False)
    width = models.IntegerField(default=480)
    height = models.IntegerField(default=270)
    coord_x = models.IntegerField(default=0) 
    coord_y = models.IntegerField(default=0)
    shifted_index = models.IntegerField(null=True, default=None)
    isBrowser = models.BooleanField(default=False)
    urlBrowser = models.CharField(max_length=255, blank=True, default='')
    isActive = models.BooleanField(default=True)
    isAlarm = models.BooleanField(default=False)
    isRolling = models.BooleanField(default=False)
    timerRolling = models.IntegerField(default=5)
    timeout = models.DateTimeField(default=None, null=True, blank=True)  # Added 'timeout' field
    visualizzazione = models.IntegerField(default=VISUALIZZAZIONE['OPENGL']) #es. 0 = opengl, 1 = browser, etc.
    enableLogo = models.BooleanField(default=False)
    enableAlarmIcon = models.BooleanField(default=False)
    enableWatermark = models.BooleanField(default=False)
    logoPath = models.CharField(max_length=255, blank=True, default='')
    alarmIconPath = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['window_id']

class RequestedWindow(models.Model):
    window_id = models.IntegerField(primary_key=True)
    stream = models.CharField(max_length=255, blank=True, default='')
    labelText = models.CharField(max_length=255, blank=True, default='')
    zoom = models.IntegerField(default=1)
    isZoom = models.BooleanField(default=False)
    width = models.IntegerField(default=480)
    height = models.IntegerField(default=270)
    coord_x = models.IntegerField(default=0) 
    coord_y = models.IntegerField(default=0)
    shifted_index = models.IntegerField(null=True, default=None)
    isBrowser = models.BooleanField(default=False)
    urlBrowser = models.CharField(max_length=255, blank=True, default='')
    isActive = models.BooleanField(default=True)
    isAlarm = models.BooleanField(default=False)
    isRolling = models.BooleanField(default=False)
    timerRolling = models.IntegerField(default=5)
    timeout = models.DateTimeField(default=None, null=True, blank=True)  # Added 'timeout' field
    visualizzazione = models.IntegerField(default=VISUALIZZAZIONE['OPENGL']) #es. 0 = opengl, 1 = browser, etc.
    enableLogo = models.BooleanField(default=False)
    enableAlarmIcon = models.BooleanField(default=False)
    enableWatermark = models.BooleanField(default=False)
    logoPath = models.CharField(max_length=255, blank=True, default='')
    alarmIconPath = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['window_id']

class BackupWindow(models.Model):
    window_id = models.IntegerField(primary_key=True)
    stream = models.CharField(max_length=255, blank=True, default='')
    labelText = models.CharField(max_length=255, blank=True, default='')
    zoom = models.IntegerField(default=1)
    isZoom = models.BooleanField(default=False)
    width = models.IntegerField(default=480)
    height = models.IntegerField(default=270)
    coord_x = models.IntegerField(default=0) 
    coord_y = models.IntegerField(default=0)
    shifted_index = models.IntegerField(null=True, default=None)
    isBrowser = models.BooleanField(default=False)
    urlBrowser = models.CharField(max_length=255, blank=True, default='')
    isActive = models.BooleanField(default=True)
    isAlarm = models.BooleanField(default=False)
    isRolling = models.BooleanField(default=False)
    timerRolling = models.IntegerField(default=5)
    timeout = models.DateTimeField(default=None, null=True, blank=True)  # Added 'timeout' field
    visualizzazione = models.IntegerField(default=VISUALIZZAZIONE['OPENGL']) #es. 0 = opengl, 1 = browser, etc.
    enableLogo = models.BooleanField(default=False)
    enableAlarmIcon = models.BooleanField(default=False)
    enableWatermark = models.BooleanField(default=False)
    logoPath = models.CharField(max_length=255, blank=True, default='')
    alarmIconPath = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['window_id']

class ImageModel(models.Model):
    image = models.ImageField(upload_to='images/')
    scope = models.IntegerField(choices=[(v, k) for k, v in IMAGE_SCOPE.items()], default=IMAGE_SCOPE['NONE'])
    selected = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class State(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    windows_number = models.IntegerField(default=16)
    active_windows = models.IntegerField(default=16)
    alarm_windows = models.IntegerField(default=0)
    alarm_border_color = ColorField(default="#FF0000")
    alarm_border_thickness = models.IntegerField(default=5)
    mode = models.IntegerField(default=0)
    browserUrl = models.CharField(max_length=255, blank=True, default='')
    isActive = models.BooleanField(default=True)
    id = models.AutoField(primary_key=True)
    
    class Meta:
        ordering = ['created']

class Api_calls(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=50)
    data = models.JSONField(max_length=1024)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        ordering = ['created']

class Delta(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    call_id = models.CharField(max_length=36)
    window_id = models.IntegerField()
    windows_column_name = models.CharField(max_length=50, blank=True)
    readState = models.BooleanField()
    id = models.AutoField(primary_key=True)

    class Meta:
        ordering = ['created']
