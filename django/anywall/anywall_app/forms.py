from django import forms
from .models import ImageModel

class ImageForm(forms.ModelForm):
    image = forms.ImageField()
    
    class Meta:
        model = ImageModel
        fields = ('image', 'scope')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scope'].widget.attrs.update({'class': 'custom-select'})
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if not image.name.endswith('.png'):
                raise forms.ValidationError("Only PNG images are allowed")
        return image
