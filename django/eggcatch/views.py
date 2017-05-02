from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.db.models import Count, Sum
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

import uuid

import datetime
from datetime import timedelta
from django.utils import timezone

from .models import Egg, Player, Catch

# Create your views here.

def current_player(request):
    if 'player_id' not in request.COOKIES:
        return None

    player_id = request.COOKIES['player_id']
    
    try:
        player = Player.objects.get(id=player_id)
        return player
    except:
        pass

    return None

def catch_action(request):

    print(request.POST)

    player = None

    code = request.POST['code']

    if 'player_id' in request.POST:
        player_id = request.POST['player_id']

        try:
            player = Player.objects.get(id=player_id)
            response = HttpResponseRedirect(reverse('egg', kwargs={'code': code}))
            response.set_cookie('player_id', player.id)
            return response
        except:
            pass

    if 'player_name' in request.POST:
        player_name = request.POST['player_name']

        if len(player_name.strip()) == 0:
            return HttpResponseRedirect(reverse('egg', kwargs={'code': code}))

        try:
            player = Player.objects.get(name=player_name)
        except:
            player = Player(name=player_name)
            player.save()

        response = HttpResponseRedirect(reverse('egg', kwargs={'code': code}))
        response.set_cookie('player_id', player.id, max_age=60*60*24*30) # 1 month
        return response

    return logout(self)

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.

def player_detail(request, id):

    player = get_object_or_404(Player, id=id)
    catches = Catch.objects.filter(player=player).order_by('-date')

    return render(request, 'player_detail.html', {'player': player, 'catches': catches})

def logout(request):
    response = HttpResponseRedirect(reverse('index', kwargs={}))
    response.delete_cookie('player_id')
    return response

def player_eurochicken(request, code):
    player = current_player(request)
    if not player:
        return HttpResponseRedirect(reverse('index', kwargs={}))

    if player.code_eurochicken != code:
        return HttpResponseRedirect(reverse('index', kwargs={}))
    
    (catch, just_caught) = player.pickup_eurochicken_catch(code)
    if not catch:
        print "-- could not pickup ec with code"
        return HttpResponseRedirect(reverse('index', kwargs={}))        

    catches = Catch.objects.filter(egg=catch.egg)

    return render(request, 'egg_detail.html', {'allow_catch':True, 'egg': catch.egg, 'player':player, 'catch':catch, 'just_caught':just_caught, 'catches':catches})

def index(request):
    
    player = None
    catches = []
    players = []
    player_name = None

    player = current_player(request)
    if player:
        player.setup_eurochicken_if_needed()

    if 'player_id' in request.COOKIES and not player:
        print("player %s does not exist" % player_name)
        response = HttpResponseRedirect(reverse('index', kwargs={}))
        response.delete_cookie('player_id')
        return response

    catches = Catch.objects.order_by("-date")[:5]

    #players_by_eggs = Player.objects.all().annotate(num_catch=Count('catch')).order_by('-num_catch')[:10]

    players_by_eggs_and_score = Player.objects.all().annotate(eggs=Count('catch'), score=Sum('catch__egg__points')).order_by('-eggs', '-score')[:15] # TODO: add 'catch__date'

    return render(
        request,
        'index.html',
        {
            'player':player,
            'players_by_eggs_and_score': players_by_eggs_and_score,
            'catches': catches
        }
    )

def egg_detail_from_id(request, id):

    player = current_player(request)

    egg = get_object_or_404(Egg, id=id)

    catch = Catch.objects.filter(player=player, egg=egg).first()

    catches = Catch.objects.filter(egg=egg).order_by("-date")

    return render(request, 'egg_detail.html', {'allow_catch':False, 'egg': egg, 'player':player, 'catch':catch, 'just_caught':False, 'catches':catches})

def players(request):

    #if not request.user.is_superuser:
    #    response = HttpResponseRedirect(reverse('index', kwargs={}))
    #    return response

    if not current_player(request):
        return HttpResponseRedirect(reverse('index'))
    
    players_by_eggs_and_score = Player.objects.all().annotate(eggs=Count('catch'), score=Sum('catch__egg__points')).order_by('-eggs', '-score')

    return render(request, 'players.html', {'players': players_by_eggs_and_score})

def faq(request):

    return render(request, 'faq.html')

def eggs(request):

    #if not request.user.is_superuser:
    #    response = HttpResponseRedirect(reverse('index', kwargs={}))
    #    return response
    
    if not current_player(request):
        return HttpResponseRedirect(reverse('index'))

    eggs = Egg.objects.all().annotate(catch_count=Count('catch')).order_by('catch_count')

    return render(request, 'eggs.html', {'eggs': eggs})

def eggs_codes(request):

    if not request.user.is_superuser:
        response = HttpResponseRedirect(reverse('index', kwargs={}))
        return response
    
    eggs = Egg.objects.all()

    return render(request, 'eggs_codes.html', {'eggs': eggs})

def egg_detail_from_code(request, code):
    
    player = current_player(request)

    egg = get_object_or_404(Egg, code=code)

    catch = Catch.objects.filter(player=player, egg=egg).first()

    just_caught = False
    if player and not catch:
        # TODO: ensure egg is not owned yet?
        catch = Catch(player=player, egg=egg, date=datetime.datetime.now())
        catch.save()
        just_caught = True

    catches = Catch.objects.filter(egg=egg)

    return render(request, 'egg_detail.html', {'allow_catch':True, 'egg': egg, 'player':player, 'catch':catch, 'just_caught':just_caught, 'catches':catches})

def combos(request):
    ids_separated_with_comma = request.path.split('/')[-1]
    if not ids_separated_with_comma:
        return render(request, 'combos.html', {'winners':[], 'eggs':[]})

    #    return HttpResponseRedirect(reverse('index', kwargs={}))

    ids = ids_separated_with_comma.split(',')

    eggs = map(lambda x:Egg.objects.filter(id=x).first(), ids)
    
    players = Player.objects.all().annotate(eggs=Count('catch'), score=Sum('catch__egg__points')).order_by('-eggs', '-score')

    winners = []

    for p in players:
        print "p:", p
        if p.has_eggs(eggs):
            winners.append(p)
            print "w", p
    
    return render(request, 'combos.html', {'winners':winners, 'eggs':eggs})

def api_description(request):

    return render(request, 'api.html')

@csrf_exempt
def api_catch_create(request):
    # POST /api/catch_create/

    print(request.POST)

    ## Egg

    if not 'egg_code' in request.POST:
        response = JsonResponse({"error_message":"egg_code POST param is missing"})
        response.status_code = 400
        return response

    egg_code = request.POST['egg_code']

    try:
        egg = Egg.objects.get(code=egg_code)
    except:
        response = JsonResponse({"error_message":"egg with code %s not found" % egg_code})
        response.status_code = 404
        return response

    ## Player

    if not 'player_id' in request.POST:
        response = JsonResponse({"error_message":"player_id POST param is missing"})
        response.status_code = 400
        return response

    player_id = request.POST['player_id']

    try:
        player = Player.objects.get(id=player_id)
    except:
        response = JsonResponse({"error_message":"player with id %s not found" % player_id})
        response.status_code = 404
        return response

    ## Catch

    catch = Catch.objects.filter(player=player, egg=egg).first()

    is_new_catch = False
    if not catch:
        catch = Catch(player=player, egg=egg, date=datetime.datetime.now())
        catch.save()
        is_new_catch = True

    return JsonResponse({'catch':catch.json_public_full(), 'is_new_catch':is_new_catch}, json_dumps_params={'indent': 2})

def api_player_name(request, name):
    # GET /api/players/name/:PLAYER_NAME
        
    players = Player.objects.filter(name=name)
    
    dictionaries = map(lambda p:p.json_public(), players)

    return JsonResponse(dictionaries, json_dumps_params={'indent': 2}, safe=False)

def api_player(request, id):
    # GET /api/player/:ID
        
    try:
        player = Player.objects.get(id=id)
    except:
        response = JsonResponse({"error_message":"player with id %s not found" % id})
        response.status_code = 404
        return response

    return JsonResponse(player.json_public(), json_dumps_params={'indent': 2})

def api_egg_id(request, id):
    # GET /api/egg/:ID
    
    try:
        egg = Egg.objects.get(id=id)
    except:
        response = JsonResponse({"error_message":"egg with id %s not found" % id})
        response.status_code = 404
        return response

    return JsonResponse(egg.json_public(), json_dumps_params={'indent': 2})

def api_egg_code(request, code):
    # GET /api/egg/:CODE
    
    try:
        egg = Egg.objects.get(code=code)
    except:
        response = JsonResponse({"error_message":"egg with code %s not found" % code})
        response.status_code = 404
        return response

    return JsonResponse(egg.json_public(), json_dumps_params={'indent': 2})

def api_players(request):
    # GET /api/players
    
    players = Player.objects.all()

    dictionaries = map(lambda p:p.json_public(), players)

    return JsonResponse(dictionaries, json_dumps_params={'indent': 2}, safe=False)

def api_eggs(request):
    # GET /api/eggs
    
    eggs = Egg.objects.all()

    dictionaries = map(lambda e:e.json_public(), eggs)

    return JsonResponse(dictionaries, json_dumps_params={'indent': 2}, safe=False)

def api_catches(request):
    # GET /api/catches
    
    catches = Catch.objects.all().order_by('-date')

    dictionaries = map(lambda c:c.json_public(), catches)

    return JsonResponse(dictionaries, json_dumps_params={'indent': 2}, safe=False)

def api_player_catches(request, id):
    # GET /api/player/:ID/catches
    
    try:
        player = Player.objects.get(id=id)
    except:
        response = JsonResponse({"error_message":"player with id %s not found" % id})
        response.status_code = 404
        return response

    catches = player.catch_set.order_by('-date')

    dictionaries = map(lambda c:c.json_public(), catches)

    return JsonResponse(dictionaries, json_dumps_params={'indent': 2}, safe=False)

def api_player_eurochicken(request, player_id):
    # GET /api/player/:ID/eurochicken/

    try:
        player = Player.objects.get(id=player_id)
        player.setup_eurochicken_if_needed()
    except:
        response = JsonResponse({"error_message":"player with id %s not found" % player_id})
        response.status_code = 404
        return response

    egg_ec_json = None
    egg_ec_catch_code = None
    if player.egg_eurochicken:
        egg_ec_json = player.egg_eurochicken.json_public()
        egg_ec_catch_code = player.code_eurochicken

    d = {'next_eurochicken_start':player.next_eurochicken_start(),
         'proposed_egg':egg_ec_json,
         'proposed_egg_catch_code':egg_ec_catch_code}

    return JsonResponse(d, json_dumps_params={'indent': 2}, safe=False)

def api_player_eurochicken_catch(request, player_id, code):
    # GET /api/player/:ID/eurochicken/:CODE/
    try:
        player = Player.objects.get(id=player_id)
        player.setup_eurochicken_if_needed()
    except:
        response = JsonResponse({"error_message":"player with id %s not found" % player_id})
        response.status_code = 404
        return response

    if player.code_eurochicken != code:
        response = JsonResponse({"error_message":"player cannot use eurochicken code %s" % code})
        response.status_code = 400
        return response
    
    (catch, just_caught) = player.pickup_eurochicken_catch(code)
    if not catch:
        response = JsonResponse({"error_message":"player cannot use eurochicken code %s" % code})
        response.status_code = 400
        return response

    return JsonResponse({'catch':catch.json_public_full(), 'is_new_catch':just_caught}, json_dumps_params={'indent': 2})

#class DetailView(generic.DetailView):
#    model = Egg
#    template_name = 'egg_detail.html'
