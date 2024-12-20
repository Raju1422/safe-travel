from django.contrib import admin
from authentication.models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display =('username','email','age','phone_number')

admin.site.register(CustomUser,CustomUserAdmin)