# coding=utf-8
"""
combat_tracker.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Copyright 2016, Tom Rees-Lee, <tomreeslee@gmail.com>
Licensed under the Eiffel Forum License 2.

http://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division
from sopel.tools import Ddict
import sopel.module

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

    def steal_actor_initiative(self, actor1, actor2, value):
        """Actor one steals a number of initiative points from actor 2."""
        self.add_actor_initiative(actor1, value)
        self.add_actor_initiative(actor2, -value)

    def add_actor_initiative(self, actor, value):
        """Changes an actors initiative value according to the value"""
        new_init = actor.initiative + value
        self.set_actor_initiative(actor, new_init)

    def set_actor_initiative(self, actor, new_init):
        """Changes an actors initiative value, potentially changing its action timing.
        Actors that have not acted yet but have an initiative value higher than the current
        tick must be queued up to act next."""
        self.initiatives[actor.initiative].remove(actor)
        actor.initiative = new_init
        if actor.initiative > self.tick and not actor.has_acted:
            self.overriding_action_queue.append(actor)
        self.initiatives[actor.initiative].add(actor)

    def get_initiative_table_string(self, active_tick_only=False):
        """Returns a formatted table of current initiatives"""
        header = "[Round: "+str(self.round)+" - Tick: "+str(self.tick)+"]"
        final_string = header
        keys = [self.tick] if active_tick_only else sorted(list(self.initiatives.keys()), reverse=True)
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


__SCENES__ = Ddict()
"""
__SCENES__ is just a dictionary for holding data on active scene data. Is there a better way?
"""

@sopel.module.commands("startscene")
@sopel.module.commands("sscene")
@sopel.module.example(".sscene", "Started Scene: [CHANNEL_NAME]")

def start_scene(bot, trigger):
    """Starts a new scene in the sending channel."""
    if trigger.is_privmsg:
        return bot.reply("I don't support starting scenes through private messages. Stick to a channel, please.")

    scene_name = trigger.sender

    if scene_name in __SCENES__:
        return bot.reply("A scene has already started in this channel")

    __SCENES__[scene_name] = Scene()
    return bot.reply("Started Scene: "+scene_name)

@sopel.module.commands("endscene")
@sopel.module.commands("escene")
@sopel.module.example(".escene", "Ended Scene: [CHANNEL_NAME]")

def end_scene(bot, trigger):
    """Ends the current scene in the sending channel."""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    del __SCENES__[scene_name]
    return bot.reply("Ended Scene: "+scene_name)

@sopel.module.commands("loadscene")
@sopel.module.commands("lscene")
@sopel.module.example(".lscene SCENE_NAME", "Loaded Scene: SCENE_NAME in channel [CHANNEL_NAME]")

def load_scene(bot, trigger):
    """Loads the scene for the name given in the current channel from
    its previous state."""
    scene_name = trigger.sender
    if scene_name in __SCENES__:
        return bot.reply("A scene has already started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("savescene")
@sopel.module.example(".savescene SCENE_NAME", "Saved Scene: SCENE_NAME from channel [CHANNEL_NAME]")

def save_scene(bot, trigger):
    """Saves the scene for the name given in the current channel.
    Scene is not ended, and will be autosaved when it is."""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("addactor")
@sopel.module.commands("aa")
@sopel.module.example(".aa Actor 7", "Actor added to [CHANNEL_NAME] Scene at 7 Initiative")
@sopel.module.example(".aa Actor", "Actor added to [CHANNEL_NAME] Scene at 0 Initiative")

def add_actor(bot, trigger):
    """Adds an actor, with a unique name, to the current scene."""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("removeactor")
@sopel.module.commands("ra")
@sopel.module.commands("kill")
@sopel.module.example(".ra Actor", "Actor removed from [CHANNEL_NAME]")

def remove_actor(bot, trigger):
    """Adds an actor, with a unique name, to the current scene."""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("init")
@sopel.module.example(".init Actor +7", "Actor gained 7 Initiative")
@sopel.module.example(".init Actor 7", "Actor set to 7 Initiative")
@sopel.module.example(".init Actor -7", "Actor lost 7 Initiative")
@sopel.module.example(".init Actor", "Actor has [INITIATIVE] Initiative")

def adjust_init(bot, trigger):
    """Adjusts initiative for an actor in the the current scene."""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("steal")
@sopel.module.example(".steal Actor1 Actor2 7", "Actor1 stole 7 init from Actor2")

def steal_init(bot, trigger):
    """One actor steals initiative from another"""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    return bot.reply("Not Implemented Yet")

@sopel.module.commands("showinit")
def show_init(bot, trigger):
    """Displays list of actors and their initiatives"""
    scene_name = trigger.sender
    if scene_name not in __SCENES__:
        return bot.reply("No scene has started in this channel")
    scene = __SCENES__[scene_name]
    table_string = scene.get_initiative_table_string
    return bot.reply(table_string)

#Tests
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
