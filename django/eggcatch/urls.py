from django.conf.urls import url

from . import views

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^eggs/$', views.eggs, name='eggs'),
    url(r'^eggs_codes/$', views.eggs_codes, name='eggs_codes'),
    url(r'^egg/catch_action/$', views.catch_action, name='catch_action'),
    url(r'^egg/(?P<code>[a-z0-9]{32})/$', views.egg_detail_from_code, name='egg'),
    url(r'^egg/(?P<id>[0-9]+)/$', views.egg_detail_from_id, name='egg'),
    url(r'^player/(?P<id>[0-9]+)/$', views.player_detail, name='player'),
    url(r'^player/eurochicken/(?P<code>[a-z0-9]{32})/$', views.player_eurochicken, name='player_eurochicken'),
    url(r'^players/$', views.players, name='players'),
    url(r'^logout/$', views.logout, name='logout'),

    url(r'^combos/.*$', views.combos, name='combos'),

    url(r'^api/$', views.api_description, name='api_description'),
    url(r'^api/players/name/(?P<name>.*)/$', views.api_player_name, name='api_player_name'),
    url(r'^api/catch_create/$', views.api_catch_create, name='api_catch_create'),
    url(r'^api/egg/(?P<code>[a-z0-9]{32})/$', views.api_egg_code, name='api_egg_code'),
    url(r'^api/egg/(?P<id>[0-9]+)/$', views.api_egg_id, name='api_egg_id'),
    url(r'^api/player/(?P<id>[0-9]+)/catches/$', views.api_player_catches, name='api_player_catches'),
    url(r'^api/player/(?P<id>[0-9]+)/$', views.api_player, name='api_player'),
    url(r'^api/eggs/$', views.api_eggs, name='api_eggs'),
    url(r'^api/players/$', views.api_players, name='api_players'),
    url(r'^api/catches/$', views.api_catches, name='api_catches'),

    url(r'^api/player/(?P<player_id>[0-9]+)/eurochicken/$', views.api_player_eurochicken, name='api_player_eurochicken'),
    url(r'^api/player/(?P<player_id>[0-9]+)/eurochicken/(?P<code>[a-z0-9]{32})/$', views.api_player_eurochicken_catch, name='api_player_eurochicken_catch')
 ]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
