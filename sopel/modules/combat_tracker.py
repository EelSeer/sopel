# coding=utf-8
"""
combat_tracker.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Copyright 2016, Tom Rees-Lee, <tomreeslee@gmail.com>
Licensed under the Eiffel Forum License 2.

http://sopel.chat/
"""
# from __future__ import unicode_literals, absolute_import, print_function, division
# import re
# import operator
# import sopel.module

class CombatTrackerError(Exception):
    """Errors resulting from tracker method miscalls."""
    def __init__(self, value):
        super(CombatTrackerError, self).__init__()
        self.value = value
    def __str__(self):
        return repr(self.value)

class Actor:
    """An actor is a entity that takes actions within a scene."""
    def __init__(self, charname, initiative=0, notes=""):
        self.initiative = initiative
        self.charname = charname
        self.notes = notes
        self.has_acted = False

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.charname == other.charname
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_pretty_status(self):
        """String displaying all relevant information about the actor."""
        status = self.charname+" status - Init: "+str(self.initiative)
        if self.notes:
            status = status + " Notes: "+self.notes
        return self.charname+" status - Init: "+str(self.initiative)+" - Notes: "+self.notes

    def get_init_string(self):
        """Short string displaying initiative only"""
        return self.charname+": "+str(self.initiative)

class Scene:
    """A Scene is a unique action scene containing a number of actors,
    which act in a order defined by their initiative count."""

    def __init__(self, name=""):
        self.initiatives = {} #key = init, value = []<Actor>
        self.actors = {} #key = charname, value = Actor
        self.name = name
        self.overriding_action_queue = []
        self.round = 0
        self.tick = 0

    def add_actor(self, actor):
        """Adds a new actor object to the scene"""
        if actor.charname in self.actors:
            return False
        self.actors[actor.charname] = actor
        if actor.initiative not in self.initiatives:
            self.initiatives[actor.initiative] = []
        self.initiatives[actor.initiative].append(actor)
        return True

    def remove_actor(self, actor):
        """Removes the actor with the given name from the scene"""
        if actor.charname in self.actors:
            initiative = actor.initiative
            del self.actors[actor.charname]
            actor_list = self.initiatives[initiative]
            actor_list.remove(actor)
            return True
        else:
            return False

    def new_round(self):
        """Begins a new round by refreshing has_acted status of all actors, and setting the tick
        to the actor with the highest initiative."""
        if not len(self.actors):
            return False #No actors!

        if len(self.overriding_action_queue.count):
            return False #All overriding actions should be done before a new round begins.

        self.round = self.round + 1
        keys = self.initiatives.keys().sort()
        self.tick = keys[0]
        for actor in self.actors:
            actor.has_acted = False

    def actor_initiative_change(self, actor, modifier):
        """Changes an actors initiative value, potentially changing its action timing.
        Actors that have not acted yet but have an initiative value higher than the current
        tick must be queued up to act next."""
        self.initiatives[actor.initiative].remove(actor)
        actor.initiative = actor.initiative + modifier
        if actor.initiative > self.tick and not actor.has_acted:
            self.overriding_action_queue.append(actor)
        self.initiatives[actor.initiative].add(actor)

    def get_initiative_table_string(self):
        """Returns a formatted table of current initiatives"""
        header = "[Round: "+str(self.round)+" - Tick: "+str(self.tick)+"]"
        final_string = header
        keys = sorted(list(self.initiatives.keys()), reverse=True)
        table = ""
        for initiative in keys:
            for actor in self.initiatives[initiative]:
                table = table+("\n"+actor.get_init_string())
                if initiative is self.tick:
                    table = table + " [Active]"
        final_string = final_string + table
        return final_string

    def get_all_actor_status(self):
        """Displays a formatted table of all current actors in scene"""
        header = "Round: "+self.round+" - Tick: "+self.tick
        final_string = header
        return final_string

def tests():
    """Runs Tests"""
    initiative_table_test()
    add_remove_actor_test()

def add_remove_actor_test():
    """Tests add/remove actor methods."""
    scene = Scene()
    lee = Actor("Lee", 3, "Singer")
    scene.add_actor(lee)
    scene.remove_actor(lee)
    if len(scene.actors):
        print("Add_Remove_Actor_Test Failed")

def initiative_table_test():
    """Tests displaying initiative table"""
    scene = Scene()
    scene.tick = 3
    akeha = Actor("Akeha", 6, "Samurai")
    akeha.has_acted = True
    lee = Actor("Lee", 3, "Singer")
    vol = Actor("Vol", 1, "Sopko")
    scene.add_actor(lee)
    scene.add_actor(akeha)
    scene.add_actor(vol)
    print(scene.get_initiative_table_string())
