from django.contrib import admin

# Import models
from .models import User, CaseLoadUser, Referral, Resource, Tag, Organization

# Register models
admin.site.register(User)
admin.site.register(CaseLoadUser)
admin.site.register(Referral)
admin.site.register(Resource)
admin.site.register(Tag)
admin.site.register(Organization)