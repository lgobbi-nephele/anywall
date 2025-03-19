from rest_framework import serializers
from anywall_app.models import *
from django.utils import timezone
from colorfield.fields import ColorField
import re

REGEX = r'^[\w\s,\\/:/.\-]+$'

class ScreenShareWindowSerializer(serializers.Serializer):
    window_id = serializers.IntegerField(default=0)

    class Meta:
        fields = ['check']

class BrowserWindowSerializer(serializers.Serializer):
    window_id = serializers.IntegerField(default=0)
    urlBrowser = serializers.CharField(max_length=255, allow_blank=True, default='')
    
    def validate_urlBrowser(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    class Meta:
        fields = ['check']

class AlarmExpiredSerializer(serializers.Serializer):
    check = serializers.BooleanField(default=True)

    class Meta:
        fields = ['check']

class AlarmClearSerializer(serializers.Serializer):
    clear = serializers.BooleanField(default=True)

    class Meta:
        fields = ['clear']

class AlarmWindowSerializer(serializers.Serializer):
    stream = serializers.CharField(max_length=255)
    labelText = serializers.CharField(max_length=255, allow_blank=True, default='')
    timer = serializers.IntegerField(default=30) # secondi
    enableAlarmIcon = serializers.BooleanField(default=False)

    def validate_stream(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_labelText(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value

    class Meta:
        model = Window
        fields = ['stream', 'labelText', 'timer', 'enableAlarmIcon']

class CustomColorField(serializers.Field):
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        try:
            alarm_border_color = ColorField().to_python(data)
            return alarm_border_color
        except ValueError:
            raise serializers.ValidationError("Invalid color format")

class AlarmStateSerializer(serializers.Serializer):
    alarm_border_color = CustomColorField(default='#FF0000')
    alarm_border_thickness = serializers.IntegerField(default=5)

    class Meta:
        model = State
        fields = ['alarm_border_color', 'alarm_border_thickness']  # Add other fields as needed

class AlarmSerializer(serializers.Serializer):
    alarm_window = AlarmWindowSerializer()
    alarm_state = AlarmStateSerializer()

    class Meta:
        fields = ['alarm_window', 'alarm_state']

    def create(self, validated_data):
        alarm_window_data = validated_data.pop('alarm_window')
        alarm_state_data = validated_data.pop('alarm_state_data')

        return {'alarm_window_data': alarm_window_data, 'alarm_state_data': alarm_state_data}

class SwitchSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=VISUALIZZAZIONE, allow_blank=True)

class ResetSerializer(serializers.Serializer): # safetyconf
    isReset = serializers.BooleanField()

class ChangeLayoutSerializer(serializers.Serializer):
    windows_number = serializers.IntegerField()


class StateSerializer(serializers.Serializer):
    windows_number = serializers.IntegerField()
    active_windows = serializers.IntegerField()
    alarm_windows = serializers.IntegerField()
    alarm_border_color = CustomColorField()
    alarm_border_tickness = models.IntegerField(default=5)
    visualizzazione = serializers.IntegerField() #es. 0 = opengl, 1 = browser, etc.
    url = serializers.CharField(max_length=255, allow_blank=True, default='')
    state = serializers.JSONField()

    def validate_url(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value

class WindowSerializer(serializers.ModelSerializer):
    window_id = serializers.IntegerField(default=0)
    stream = serializers.CharField(max_length=255, allow_blank=True, default='')
    labelText = serializers.CharField(max_length=255, allow_blank=True, default='')
    zoom = serializers.IntegerField(default=1)
    isZoom = serializers.BooleanField(default=False)
    width = serializers.IntegerField(default=480)
    height = serializers.IntegerField(default=270)
    coord_x = serializers.IntegerField(default=0) 
    coord_y = serializers.IntegerField(default=0)
    isBrowser = serializers.BooleanField(default=False)
    urlBrowser = serializers.CharField(max_length=255, allow_blank=True, default='')
    isActive = serializers.BooleanField(default=True)
    isAlarm = serializers.BooleanField(default=False)
    isRolling = serializers.BooleanField(default=False)
    timerRolling = serializers.IntegerField(default=5)
    timeout = serializers.DateTimeField(allow_null=True)  # Added 'timeout' field
    visualizzazione = serializers.IntegerField(default=0) #es. 0 = opengl, 1 = browser, etc.
    enableLogo = serializers.BooleanField(default=False)
    enableWatermark = serializers.BooleanField(default=False)

    def validate_stream(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_labelText(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_urlBrowser(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    class Meta:
        model = Window
        fields = ['window_id', 'stream', 'isAlarm', 'zoom', 'timeout', 'timer', 'enableLogo', 'enableWatermark']

    def create(self, validated_data):
        timer = validated_data.pop('timer', None)
        if timer is not None:
            timeout = datetime.datetime.now() + datetime.timedelta(seconds=timer)
            timeout = timezone.make_aware(timeout, timezone.get_current_timezone())
            validated_data['timeout'] = timeout
        return super().create(validated_data)

class RequestedWindowSerializer(serializers.ModelSerializer):
    window_id = serializers.IntegerField(default=0)
    stream = serializers.CharField(max_length=255, allow_blank=True, default='')
    labelText = serializers.CharField(max_length=255, allow_blank=True, default='')
    zoom = serializers.IntegerField(default=1)
    isZoom = serializers.BooleanField(default=False)
    width = serializers.IntegerField(default=480)
    height = serializers.IntegerField(default=270)
    coord_x = serializers.IntegerField(default=0) 
    coord_y = serializers.IntegerField(default=0)
    isBrowser = serializers.BooleanField(default=False)
    urlBrowser = serializers.CharField(max_length=255, allow_blank=True, default='')
    isActive = serializers.BooleanField(default=True)
    isAlarm = serializers.BooleanField(default=False)
    isRolling = serializers.BooleanField(default=False)
    timerRolling = serializers.IntegerField(default=5)
    timeout = serializers.DateTimeField(allow_null=True)  # Added 'timeout' field
    visualizzazione = serializers.IntegerField(default=0) #es. 0 = opengl, 1 = browser, etc.
    enableLogo = serializers.BooleanField(default=False)
    enableWatermark = serializers.BooleanField(default=False)

    def validate_stream(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_labelText(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_urlBrowser(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    class Meta:
        model = RequestedWindow
        fields = ['window_id', 'stream', 'isAlarm', 'zoom', 'timeout', 'timer', 'enableWatermark']

    def create(self, validated_data):
        timer = validated_data.pop('timer', None)
        if timer is not None:
            timeout = datetime.datetime.now() + datetime.timedelta(seconds=timer)
            timeout = timezone.make_aware(timeout, timezone.get_current_timezone())
            validated_data['timeout'] = timeout
        return super().create(validated_data)

class DeltaSerializer(serializers.ModelSerializer):
    call_id = serializers.IntegerField()
    window_id = serializers.IntegerField()
    windows_column_name = serializers.CharField(max_length=50, allow_blank=True)
    readState = serializers.BooleanField()

    def validate_windows_column_name(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value

class ChangeStreamSerializer(serializers.ModelSerializer):
    window_id = serializers.IntegerField()
    stream = serializers.CharField(max_length=255, allow_blank=True)
    labelText = serializers.CharField(max_length=255, allow_blank=True, default='')
    enableLogo = serializers.BooleanField(default=False)
    enableWatermark = serializers.BooleanField(default=False)

    def validate_stream(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    def validate_labelText(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value
    
    class Meta:
        model = RequestedWindow
        fields = ['window_id', 'stream', 'labelText', 'enableLogo', 'enableWatermark']

class ZoomSerializer(serializers.ModelSerializer):
    window_id = serializers.IntegerField()
    zoom = serializers.IntegerField(default=1)

    class Meta:
        model = RequestedWindow
        fields = ['window_id', 'zoom']

class BrowserSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=255, allow_blank=True, default='')

    def validate_url(self, value):
        if not re.match(REGEX, value):  # Only allow letters, numbers, spaces, commas, and hyphens
            raise serializers.ValidationError("Special characters are not allowed.")
        return value