from rest_framework import generics
from rest_framework.response import Response

from anywall_app.models import *
from anywall_app.serializers import *
from anywall_app.service import *

import base64
import mimetypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import *
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
import json
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

@csrf_exempt
@login_required
def signaling(request):
    
    if request.method == 'POST':
        message = json.loads(request.body)
        message_type = message.get('type')
        content = json.dumps(message)

        # Salva il messaggio di segnalazione nel database
        signaling_message = SignalingMessage.objects.create(
            message_type=message_type,
            content=content
        )

        return JsonResponse({'status': 'success', 'message_id': signaling_message.id})
    return JsonResponse({'status': 'failed'})

@login_required
def get_offer(request):
    
    try:
        offer_message = SignalingMessage.objects.filter(message_type='offer').latest('timestamp')
        offer = json.loads(offer_message.content)
        return JsonResponse({'offer': offer['offer']})
    except SignalingMessage.DoesNotExist:
        return JsonResponse({'error': 'No offer found'}, status=404)

@login_required
def get_candidates(request):
    
    candidates = SignalingMessage.objects.filter(message_type='candidate').order_by('timestamp')
    candidate_list = [json.loads(candidate.content)['candidate'] for candidate in candidates]
    return JsonResponse({'candidates': candidate_list})

# @csrf_exempt
# def signaling(request):
    
#     if request.method == 'POST':
#         message = json.loads(request.body)
#         # Gestisci il messaggio di segnalazione qui
#         # Puoi memorizzare l'offerta e i candidati ICE in un database o in memoria
#         return JsonResponse({'status': 'success'})
#     return JsonResponse({'status': 'failed'})

# tutto da disaccoppiare in service. Aggiormento di tutte le altre tabelle.
# view solo collezione campi e salvataggio in api_call

@login_required
def get_images_by_scope(request):
    
    scope = request.GET.get('scope')
    images = list(ImageModel.objects.filter(scope=scope))
    connection.close()
    
    def image_to_base64(image_data):
        try:
            encoded_string = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type
            mime_type = mimetypes.guess_type("example.jpg")[0]  # Use a dummy filename
            
            if not mime_type:
                logger.warning("Unable to determine MIME type for image")
                return None
            
            return f"data:{mime_type};base64,{encoded_string}"
        
        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            return None
    
    image_list = []
    for img in images:
        
        try:
            with open(img.image.path, "rb") as image_file:
                encoded_image = image_to_base64(image_file.read())
                
                if encoded_image:
                    image_list.append({
                        'id': img.id,
                        'image': str(img.image.path),
                        'preview': encoded_image
                    })
                else:
                    logger.warning(f"Failed to encode image preview for ID: {img.id}")
        
        except FileNotFoundError:
            logger.error(f"Image file not found at path: {img.image.path}")
        except Exception as e:
            logger.error(f"Unexpected error processing image {img.id}: {str(e)}")
    
    logger.info(f"Processed {len(image_list)} images out of {len(images)}")
    return JsonResponse(image_list, safe=False)

# def get_images_by_scope(request):
    
#     scope = request.GET.get('scope')
#     images = ImageModel.objects.filter(scope=scope)
    
#     previews = []
#     for image in images:
#         preview_url = f"file:///usr/local/etc/Anywall/resources/media/{image.image}"
#         previews.append({
#             'id': image.id,
#             'image': str(image.image.path),
#             'preview': preview_url
#         })
    
#     return JsonResponse(previews, safe=False)

@login_required
def select_image(request):
    
    
    if request.method == 'POST':
        image_scope = int(request.POST.get("image_scope"))
        selected_image = request.POST.get('images')
        window_id = request.POST.get('window_id')

        if window_id is not None:
            window_id = int(window_id)

        try:
            if selected_image:
                # Unpack the selected image value
                image_id, image_filename = selected_image.split(',')
                
                # solve image filename here
                print(f"selected_image: {selected_image}")
                
                # Convert image_id to int (assuming it's numeric)
                image_id = int(image_id)
            
            api_call = Api_calls(name='select-image/', data={"image_scope":image_scope, "window_id":window_id})

            if window_id is not None:
                # modifica finestra
                if image_scope == 0 or image_scope == 1 or image_scope == 4:
                    raise Exception
                if image_scope == 2:
                    if selected_image:
                        requested_window_instance, created = RequestedWindow.objects.update_or_create(
                                                                                window_id=window_id,
                                                                                defaults={"logoPath":image_filename}
                                                                                )
                    else:
                        requested_window_instance, created = RequestedWindow.objects.update_or_create(
                                                                                window_id=window_id,
                                                                                defaults={"logoPath":""}
                                                                                )
                if image_scope == 3:
                    if selected_image:
                        requested_window_instance, created = RequestedWindow.objects.update_or_create(
                                                                                window_id=window_id,
                                                                                defaults={"alarmIconPath":image_filename}
                                                                                )
                    else:
                        requested_window_instance, created = RequestedWindow.objects.update_or_create(
                                                                                window_id=window_id,
                                                                                defaults={"alarmIconPath":""}
                                                                                )
                makeDeltaRows(None, requested_window_instance, api_call)
            else:
                if image_scope == 0:
                    raise Exception
                if image_scope == 1 or image_scope == 4:
                    images_by_selected_scope = ImageModel.objects.filter(scope=image_scope)
                    if selected_image:
                        for im in images_by_selected_scope:
                            ImageModel.objects.update_or_create(id=im.id, defaults={"selected": (im.id == image_id)})
                    else:
                        for im in images_by_selected_scope:
                            ImageModel.objects.update_or_create(id=im.id, defaults={"selected": False})
            api_call.save()
            
            connection.close()
            return redirect('success')  # Redirect after successful submission
        except ValueError:
            # Handle invalid format
            print(f"Invalid image selection format: {selected_image}")
        except ImageModel.DoesNotExist:
            print(f"No image found with ID: {image_id}")

    
    # form = ImageForm()
    images_list = ImageModel.objects.all()
    connection.close()
    context = {'images':images_list, 'IMAGE_SCOPE':IMAGE_SCOPE}
    return render(request, 'select_image.html', context)

@login_required
def upload_image(request):
    
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = ImageForm()
    return render(request, 'upload_image.html', {'form': form})

@login_required
def success(request):
    
    return render(request, 'success.html')

@login_required
def sender(request):
    
    return render(request, 'sender.html')

@login_required
def receiver(request):
    
    return render(request, 'receiver.html')

@login_required
def setting(request):
    
    return render(request, 'setting.html', {
        'SERVER_IP': settings.SERVER_IP
    })

@login_required
def clock_view(request):
    
    return render(request, 'clock_view.html')

class CustomLoginView(LoginView):
    template_name='login.html'

class BrowserWindowAPIView(generics.GenericAPIView):
    serializer_class = BrowserWindowSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='browser-window', data=serializer.validated_data)
            # try:
            response = browserWindowAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
            # except Exception as e:
            #     # Handle any exceptions raised during save, e.g., integrity errors, validation failures, etc.
            #     print(f"Failed to save Api_calls object: {e}")
        return Response(serializer.errors, status=400)
   
class ScreenShareWindowAPIView(generics.GenericAPIView):
    serializer_class = ScreenShareWindowSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='screen-share-window', data=serializer.validated_data)
            # try:
            response = screenShareWindowAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
            # except Exception as e:
            #     # Handle any exceptions raised during save, e.g., integrity errors, validation failures, etc.
            #     print(f"Failed to save Api_calls object: {e}")
        return Response(serializer.errors, status=400)

class AlarmExpiredAPIView(generics.GenericAPIView):
    serializer_class = AlarmExpiredSerializer    
    #permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='alarm/expired/', data=serializer.validated_data)
            # try:
            response = alarmExpiredAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
            # except Exception as e:
            #     # Handle any exceptions raised during save, e.g., integrity errors, validation failures, etc.
            #     print(f"Failed to save Api_calls object: {e}")
        return Response(serializer.errors, status=400)

class AlarmClearAPIView(generics.GenericAPIView):
    serializer_class = AlarmClearSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='alarm/clear', data=serializer.validated_data)
            # try:
            response = alarmClearAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
            # except Exception as e:
            #     # Handle any exceptions raised during save, e.g., integrity errors, validation failures, etc.
            #     print(f"Failed to save Api_calls object: {e}")
        return Response(serializer.errors, status=400)

class AlarmAPIView(generics.GenericAPIView):
    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='alarm', data=serializer.validated_data)
            # try:
            response = alarmAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
            # except Exception as e:
            #     # Handle any exceptions raised during save, e.g., integrity errors, validation failures, etc.
            #     print(f"Failed to save Api_calls object: {e}")
        return Response(serializer.errors, status=400)

class ChangeStreamAPIView(generics.GenericAPIView):
    serializer_class = ChangeStreamSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='changeStream', data=serializer.validated_data)
            response = changeStreamAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response

        return Response(serializer.errors, status=400)

class SwitchAPIView(generics.GenericAPIView):
    serializer_class = SwitchSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='switch', data=serializer.validated_data)
            response = switchAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response

        return Response(serializer.errors, status=400)


class ZoomAPIView(generics.GenericAPIView):
    serializer_class = ZoomSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='zoom', data=serializer.validated_data)
            response = zoomAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response

        return Response(serializer.errors, status=400)

class RestartAPIView(generics.GenericAPIView):
    serializer_class = ResetSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='reset', data=serializer.validated_data)
            # try:
            response = restartAPIService(serializer.validated_data)
            api_call.save()
            return response

        return Response(serializer.errors, status=400)

class ResetAPIView(generics.GenericAPIView):
    serializer_class = ResetSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='reset', data=serializer.validated_data)
            response = resetAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response

        return Response(serializer.errors, status=400)


class BrowserAPIView(generics.GenericAPIView):
    serializer_class = BrowserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls.objects.create(name='browser', data=serializer.validated_data)
            connection.close()
            response = browserAPIService(serializer.validated_data, api_call)
            return response
             
        return Response(serializer.errors, status=400)

class ChangeLayoutAPIView(generics.GenericAPIView):
    serializer_class = ChangeLayoutSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_call = Api_calls(name='change-layout', data=serializer.validated_data)
            response = changeLayoutAPIService(serializer.validated_data, api_call)
            api_call.save()
            return response
           
        return Response(serializer.errors, status=400)
            


class UpdateState():
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            windows_number = serializer.validated_data['windows_number']
            active_windows = serializer.validated_data['active_windows']
            alarm_windows = serializer.validated_data['alarm_windows']
            state = serializer.validated_data['state']

            # temporaneo: se stato è vuoto utilizzo stato precedente
            last_state_str = ''
            if state == '':
                last_state_entry = State.objects.latest('created')
                last_state_str = last_state_entry.state

            State.objects.create(windows_number=windows_number, active_windows=active_windows, alarm_windows=alarm_windows, state=state if state != '' else last_state_str)
            connection.close()
            return Response({'status': 'success', 'message': 'State updated successfully.'})
        return Response(serializer.errors, status=400)