from django.contrib import admin
from .models import Profile, Broadcast

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'authorization_id')

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'broadcaster', 'is_live', 'created_at')
    list_filter  = ('is_live', 'created_at', 'broadcaster')
    search_fields = ('title', 'broadcaster__username')
