from django import forms
from .models import ShareSpace


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class FileUploadForm(forms.Form):
    title = forms.CharField(max_length=100)
    file_field = MultipleFileField()
    description = forms.CharField(widget=forms.Textarea, required=False)
    visibility = forms.ChoiceField(choices=ShareSpace.VisibilityChoices.choices)
    password = forms.CharField(
        max_length=50, widget=forms.PasswordInput(), required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get("visibility")
        password = cleaned_data.get("password")

        if (
            visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED
            and not password
        ):
            raise forms.ValidationError(
                "Password is required for password-protected spaces."
            )
        return cleaned_data


class ShareSpaceAccessForm(forms.Form):
    password = forms.CharField(
        max_length=50, widget=forms.PasswordInput(), required=True
    )
