from django.contrib import admin

from .models import GoogleAuthToken, JobEmail, Label, User

# Register your models here.

admin.site.register(User)
admin.site.register(JobEmail)
admin.site.register(Label)
admin.site.register(GoogleAuthToken)
