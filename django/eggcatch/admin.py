from django.contrib import admin

# Register your models here.

from .models import Egg, Player, Catch

#admin.site.register(Egg)
admin.site.register(Player)
admin.site.register(Catch)

class EggAdmin(admin.ModelAdmin):
    list_display = ('image_tag', 'name', 'points', 'number_of_catches', 'description')
    list_display_links = ['name']
    search_fields = ['name']
    list_per_page = 100

    def image_tag(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return u'<img src="%s" height=64 />' % obj.image.url
        return None
    image_tag.allow_tags = True
    image_tag.short_description = 'Image'

admin.site.register(Egg, EggAdmin)
