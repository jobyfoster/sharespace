from django import forms
from .models import ShareSpace


class MultipleFileInput(forms.ClearableFileInput):
    # This custom file input allows for multiple files to be selected.
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    # Custom FileField to handle multiple file uploads.
    def __init__(self, *args, **kwargs):
        # Sets the widget to our custom MultipleFileInput.
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Custom cleaning method for handling multiple files.
        single_file_clean = (
            super().clean
        )  # Gets the cleaning method from the superclass
        if isinstance(data, (list, tuple)):
            # If the data is a list or tuple, clean each file in it.
            result = [single_file_clean(d, initial) for d in data]
        else:
            # If it's not a list or tuple, just clean the single file.
            result = single_file_clean(data, initial)
        return result


class FileUploadForm(forms.Form):
    # This form is for uploading files.
    title = forms.CharField(max_length=100)  # Field for the title
    file_field = MultipleFileField()  # Uses the custom field for multiple files
    description = forms.CharField(
        widget=forms.Textarea, required=False
    )  # Optional description
    # Field for selecting visibility, using predefined choices
    visibility = forms.ChoiceField(choices=ShareSpace.VisibilityChoices.choices)
    # Optional password field, used for password-protected spaces
    password = forms.CharField(
        max_length=50, widget=forms.PasswordInput(), required=False
    )

    def clean(self):
        # Custom clean method to add extra validation
        cleaned_data = super().clean()  # Cleans the data using the parent class method
        visibility = cleaned_data.get("visibility")
        password = cleaned_data.get("password")

        # Checks if a password is required for the selected visibility type
        if (
            visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED
            and not password
        ):
            # Raises a validation error if a password is required but not provided
            raise forms.ValidationError(
                "Password is required for password-protected spaces."
            )
        return cleaned_data


class ShareSpaceAccessForm(forms.Form):
    # Simple form for accessing a ShareSpace
    password = forms.CharField(
        max_length=50, widget=forms.PasswordInput(), required=True
    )
