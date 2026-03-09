from django import forms
from .models import LateCheckInPolicy
from django.core.exceptions import ValidationError
from django import forms
from .models import Course, Lesson
from django import forms
from .models import Student

class LateCheckInPolicyForm(forms.ModelForm):
    class Meta:
        model = LateCheckInPolicy
        fields = ['student', 'start_time', 'description']
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        policy_id = self.instance.id  # Get the current instance's ID

        # Check if a LateCheckInPolicy already exists for this student, excluding the current instance
        if student and LateCheckInPolicy.objects.filter(student=student).exclude(id=policy_id).exists():
            raise ValidationError(f"A late check-in policy already exists for {student.name}.")
        
        return cleaned_data


##############################################################
from django import forms
from .models import Student
import json

class StudentEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name',
            'email',
            'phone_number',
            'face_embedding',
            'roll_no',
            'address',
            'date_of_birth',
            'joining_date',
            'mother_name',
            'father_name',
            'authorized',
            'session',
            'courses',
            'department',
            'semester',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'face_embedding': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter face embedding as JSON',
            }),
            'roll_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter roll number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter mother's name"}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter father's name"}),
            'authorized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'session': forms.Select(attrs={'class': 'form-control'}),
            'courses': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'department': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'semester': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def clean_face_embedding(self):
        data = self.cleaned_data.get('face_embedding')
        try:
            # Ensure valid JSON data
            return json.loads(data)
        except (ValueError, TypeError):
            raise forms.ValidationError("Invalid JSON format for face embedding.")



##################################################################
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'session']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter course name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Enter course description'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
#################################################################
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'description', 'youtube_embed_link', 'youtube_video_url', 'video_file', 'lesson_notes']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lesson title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter lesson description'}),
            'youtube_embed_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter YouTube embed link'}),
            'youtube_video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter YouTube video URL'}),
            'video_file': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'lesson_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter lesson notes'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
#######################################################################
from django import forms
from .models import Leave

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
