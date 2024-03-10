# forms.py

from django import forms
from .models import ImageUpload

class ImageProcessingOptionsForm(forms.Form):
    group_radius = forms.IntegerField(min_value=1, initial=50)
    min_dots = forms.IntegerField(min_value=1, initial=100)
    threshold = forms.IntegerField(min_value=0, initial=60)
    circle_color = forms.CharField(initial='green')
    circle_width = forms.IntegerField(min_value=1, initial=8)

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageUpload
        fields = ('image',)

    # You can add the processing options form fields here as well if you want them all in one form
