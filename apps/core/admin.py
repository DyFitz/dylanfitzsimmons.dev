from django.conf import settings
from django.contrib import admin

admin.site.site_header = f"{settings.SITE_NAME}: site admin"
admin.site.site_title = "Site admin"
admin.site.index_title = "Content"
