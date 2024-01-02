from django import forms
from .models import UploadedFile


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ["title", "file", "description"]

    def clean_file(self):
        file = self.cleaned_data.get("file", False)
        if file:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File too large ( > 10MB )")
            return file
        else:
            raise forms.ValidationError("Couldn't read uploaded file")
