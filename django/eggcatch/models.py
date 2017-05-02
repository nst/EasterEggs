from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings

import os
import uuid
import random
import datetime
from django.utils import timezone

from PIL import Image

from django.db.models import Count, Sum

from django.contrib import admin

# Create your models here.

def get_image_path(instance, filename):
    return os.path.join("egg", str(instance.id), filename)

@python_2_unicode_compatible  # only if you need to support Python 2
class Egg(models.Model):
    name = models.CharField(max_length=64, unique=True)
    points = models.SmallIntegerField(default=10)
    code = models.CharField(max_length=32, editable=True, blank=True, unique=True)
    description = models.CharField(max_length=256, blank=True)
    comment_private = models.CharField(max_length=256, blank=True)
    image = models.ImageField(upload_to=get_image_path, blank=True, null=True)

    #slug_field = 'code'
    #slug_url_kwarg = 'code'

    #def get_object(self):
    #      return get_object_or_404(Egg, code=self.pk)

    @classmethod
    def random_caught_egg(self):
        all_caught_eggs = Egg.objects.exclude(catch=None)
        print(all_caught_eggs)
        if len(all_caught_eggs) == 0:
            print "-- -> None"
            return None

        random_egg = random.choice(all_caught_eggs)
        return random_egg

    def is_toxic(self):
        return self.points < 0

    def number_of_catches(self):
        catches = Catch.objects.filter(egg=self)
        return catches.count()

    def clean(self):
        if self.code == "":
            self.code = uuid.uuid4().hex

    def __str__(self):
        return self.name

    def image_url(self):
        if not self.image:
            return None
        return settings.HOSTNAME + self.image.url

    def json_public(self):
        return {
        'id':self.id,
        'name':self.name,
        'points':self.points,
        'description':self.description,
        'number_of_catches':self.number_of_catches(),
        'image_url':self.image_url()
        }

@python_2_unicode_compatible  # only if you need to support Python 2
class Player(models.Model):
    name = models.CharField(max_length=64, unique=True)
    last_eurochicken = models.DateTimeField('last eurochicken', default=datetime.datetime.now, blank=True, null=True)
    egg_eurochicken = models.ForeignKey(Egg, on_delete=models.CASCADE, blank=True, null=True)
    code_eurochicken = models.CharField(max_length=32, editable=True, blank=True)

    def setup_eurochicken_if_needed(self):
        next_ec = self.next_eurochicken_start()
        #print "--------- next_ec:", next_ec
        do_setup = timezone.now() > next_ec
        if do_setup and self.egg_eurochicken == None:
            self.egg_eurochicken = Egg.random_caught_egg()
            self.code_eurochicken = uuid.uuid4().hex
            self.save()
            #print "--------- egg_eurochicken", self.egg_eurochicken
            #print "-- has?", player.has_egg(free_egg)

    def pickup_eurochicken_catch(self, code):

        if code != self.code_eurochicken:
            print "-- bad ec code:", code
            return

        c = None
        just_caught = False

        if self.egg_eurochicken != None and self.egg_eurochicken not in self.eggs():
            c = Catch()
            c.player = self
            c.egg = self.egg_eurochicken
            c.date = datetime.datetime.now()
            c.save()
            just_caught = True
        elif self.egg_eurochicken != None:
            c = Catch.objects.filter(player=self, egg=self.egg_eurochicken).first()
        else:
            pass
        
        self.egg_eurochicken = None
        self.hash_eurochicken = None
        self.last_eurochicken = datetime.datetime.now()
        self.save()

        return (c, just_caught)

    def last_eurochicken_for_seconds(self):
        no_ec_for = timezone.now() - self.last_eurochicken
        return no_ec_for.seconds

    def next_eurochicken_start(self):
        return self.last_eurochicken + datetime.timedelta(hours=2)

    def has_egg(self, egg):
        qs = Catch.objects.filter(player=self, egg=egg)
        return len(qs) > 0

    def has_eggs(self, the_eggs):
        if len(the_eggs) == 0:
            return False

        for e in the_eggs:
            if not self.has_egg(e):
                return False
        return True

    def eggs(self):
        return Egg.objects.filter(catch__player=self)

    def score(self):
        d = Player.objects.filter(id=self.id).annotate(score=Sum('catch__egg__points')).values('score')[0]
        return d['score']

    def catches(self):
        return Catch.objects.filter(player=self).order_by('date')

    def number_of_eggs(self):
        return self.catch_set.all().count()

    def __str__(self):
        return self.name

    def json_public(self):
        return {'id': self.id, 'name':self.name, 'score':self.score(), 'number_of_eggs':self.number_of_eggs()}

@python_2_unicode_compatible  # only if you need to support Python 2
class Catch(models.Model):
    egg = models.ForeignKey(Egg, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    date = models.DateTimeField('catch date')

    def json_public(self):
        return {'id':self.id, 'date':self.date, 'egg_id':self.egg.id, 'player_id':self.player_id}

    def json_public_full(self):
        return {'id':self.id, 'date':self.date, 'egg':self.egg.json_public(), 'player':self.player.json_public()}

    def __str__(self):
        return self.date.strftime('%Y-%m-%d %H:%M:%S') + " " + self.player.name + " " + self.egg.name
