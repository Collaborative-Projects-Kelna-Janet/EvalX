from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Team, TeamMember, TeamSubmission

class CustomUserAdmin(UserAdmin):
    # Controls which columns display in the user list view
    list_display = ('email', 'username', 'role', 'is_staff', 'is_superuser')
    
    # Allows filtering users by role or staff status in the side panel
    list_filter = ('role', 'is_staff', 'is_superuser')
    
    # Enables password hashing fields and organizes user detail sections
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role Settings', {'fields': ('role',)}),
    )
    
    # Form layout when adding a new user directly in Django Admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Role Settings', {'fields': ('role',)}),
    )

# Register CustomUserAdmin for the User model
admin.site.register(User, CustomUserAdmin)

# Register remaining models
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(TeamSubmission)