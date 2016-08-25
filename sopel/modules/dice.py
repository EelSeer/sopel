# coding=utf-8
"""
dice.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

http://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import random
import re
import operator

import sopel.module
from sopel.tools.calculation import eval_equation


class DicePouch:
    def __init__(self, num_of_die, type_of_die, addition):
        """Initialize dice pouch and roll the dice.

        Args:
            num_of_die: number of dice in the pouch.
            type_of_die: how many faces the dice have.
            addition: how much is added to the result of the dice.
        """
        self.num = num_of_die
        self.type = type_of_die
        self.addition = addition

        self.dice = {}
        self.dropped = {}

        self.roll_dice()

    def roll_dice(self):
        """Roll all the dice in the pouch."""
        self.dice = {}
        self.dropped = {}
        for __ in range(self.num):
            number = random.randint(1, self.type)
            count = self.dice.setdefault(number, 0)
            self.dice[number] = count + 1

    def drop_lowest(self, n):
        """Drop n lowest dice from the result.

        Args:
            n: the number of dice to drop.
        """

        sorted_x = sorted(self.dice.items(), key=operator.itemgetter(0))

        for i, count in sorted_x:
            count = self.dice[i]
            if n == 0:
                break
            elif n < count:
                self.dice[i] = count - n
                self.dropped[i] = n
                break
            else:
                self.dice[i] = 0
                self.dropped[i] = count
                n = n - count

        for i, count in self.dropped.items():
            if self.dice[i] == 0:
                del self.dice[i]

    def get_simple_string(self):
        """Return the values of the dice like (2+2+2[+1+1])+1."""
        dice = self.dice.items()
        faces = ("+".join([str(face)] * times) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("+".join([str(face)] * times) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_compressed_string(self):
        """Return the values of the dice like (3x2[+2x1])+1."""
        dice = self.dice.items()
        faces = ("%dx%d" % (times, face) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("%dx%d" % (times, face) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_sum(self):
        """Get the sum of non-dropped dice and the addition."""
        result = self.addition
        for face, times in self.dice.items():
            result += face * times
        return result

    def get_number_of_faces(self):
        """Returns sum of different faces for dropped and not dropped dice

        This can be used to estimate, whether the result can be shown in
        compressed form in a reasonable amount of space.
        """
        return len(self.dice) + len(self.dropped)

    def reroll_dice(self, dice_val_to_reroll, max_dice_to_reroll=0, keep_results=False):
        """Reroll a selection of dice, discarding previous result.
        Args:
            dice_val_to_reroll: Value of dice to reroll.
            max_dice_to_reroll: Maximum dice that can be rerolled. 0 means all will be rerolled.
            keep_results: Set to True to keep previous results in dice pouch.
        """
        dice_at_value = self.dice[dice_val_to_reroll];
        dice_to_reroll = min(max_dice_to_reroll, dice_at_value)
        
        rerolled_dice = DicePouch(dice_to_reroll, self.type)

        if keep_results == False:
            self.dice[dice_val_to_reroll] -= dice_to_reroll
            self.dropped[dice_val_to_reroll] += dice_to_reroll

        for key in rerolled_dice.keys():
            if key not in self.dice.keys():
                self.dice[key] = rerolled_dice.dice[key]
            self.dice[key] += rerolled_dice.dice[key]

    def get_storyteller_result_string(self, target_num=7, double_min=10):
        successes = self.addition
        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("+".join([str(face)] * times) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        dice_str = ""
        sorted_x = sorted(self.dice.items(), key=operator.itemgetter(0))
        for i, count in sorted_x:
            if len(dice_str):
                dice_str+=(", ")
            dice_str+=(str(i)+": "+str(count))
            if i >= target_num:
                successes += count
                if i >= double_min:
                    successes += count

        plus_str = ""
        if self.addition > 0:
            plus_str+=("+ "+str(self.addition))
        if self.addition < 0:
            plus_str+=("- "+abs(str(self.addition)))

        success_str = "" 
        if successes =< 0 and 1 in self.dice.keys(): 
            success_str+="BOTCH"
        elif successes == 1:
            success_str+=("1 Success")
        else:
            success_str+=(str(successes)+" Successes")

        return "[%s] %s - %s" % (dice_str, plus_str, success_str)

def _roll_dice(bot, dice_expression):
    result = re.search(
        r"""
        (?P<dice_num>-?\d*)
        d
        (?P<dice_type>-?\d+)
        (v(?P<drop_lowest>-?\d+))?
        $""",
        dice_expression,
        re.IGNORECASE | re.VERBOSE)

    dice_num = int(result.group('dice_num') or 1)
    dice_type = int(result.group('dice_type'))

    # Dice can't have zero or a negative number of sides.
    if dice_type <= 0:
        bot.reply("I don't have any dice with %d sides. =(" % dice_type)
        return None  # Signal there was a problem

    # Can't roll a negative number of dice.
    if dice_num < 0:
        bot.reply("I'd rather not roll a negative amount of dice. =(")
        return None  # Signal there was a problem

    # Upper limit for dice should be at most a million. Creating a dict with
    # more than a million elements already takes a noticeable amount of time
    # on a fast computer and ~55kB of memory.
    if dice_num > 1000:
        bot.reply('I only have 1000 dice. =(')
        return None  # Signal there was a problem

    dice = DicePouch(dice_num, dice_type, 0)

    if result.group('drop_lowest'):
        drop = int(result.group('drop_lowest'))
        if drop >= 0:
            dice.drop_lowest(drop)
        else:
            bot.reply("I can't drop the lowest %d dice. =(" % drop)

    return dice

@sopel.module.commands("roll")
@sopel.module.commands("dice")
@sopel.module.commands("d")
@sopel.module.priority("medium")
@sopel.module.example(".roll 3d1+1", 'You roll 3d1+1: (1+1+1)+1 = 4')
@sopel.module.example(".roll 3d1v2+1", 'You roll 3d1v2+1: (1[+1+1])+1 = 2')
@sopel.module.example(".roll 2d4", 'You roll 2d4: \(\d\+\d\) = \d', re=True)
@sopel.module.example(".roll 100d1", '[^:]*: \(100x1\) = 100', re=True)
@sopel.module.example(".roll 1001d1", 'I only have 1000 dice. =(')
@sopel.module.example(".roll 1d1 + 1d1", 'You roll 1d1 + 1d1: (1) + (1) = 2')
@sopel.module.example(".roll 1d1+1d1", 'You roll 1d1+1d1: (1)+(1) = 2')
def roll(bot, trigger):
    """.dice XdY[vZ][+N], rolls dice and reports the result.

    X is the number of dice. Y is the number of faces in the dice. Z is the
    number of lowest dice to be dropped from the result. N is the constant to
    be applied to the end result.
    """
    # This regexp is only allowed to have one captured group, because having
    # more would alter the output of re.findall.
    dice_regexp = r"-?\d*[dD]-?\d+(?:[vV]-?\d+)?"

    # Get a list of all dice expressions, evaluate them and then replace the
    # expressions in the original string with the results. Replacing is done
    # using string formatting, so %-characters must be escaped.
    if not trigger.group(2):
        return bot.reply("No dice to roll.")
    arg_str = trigger.group(2)
    dice_expressions = re.findall(dice_regexp, arg_str)
    arg_str = arg_str.replace("%", "%%")
    arg_str = re.sub(dice_regexp, "%s", arg_str)

    f = lambda dice_expr: _roll_dice(bot, dice_expr)
    dice = list(map(f, dice_expressions))

    if None in dice:
        # Stop computing roll if there was a problem rolling dice.
        return

    def _get_eval_str(dice):
        return "(%d)" % (dice.get_sum(),)

    def _get_pretty_str(dice):
        if dice.num <= 10:
            return dice.get_simple_string()
        elif dice.get_number_of_faces() <= 10:
            return dice.get_compressed_string()
        else:
            return "(...)"

    eval_str = arg_str % (tuple(map(_get_eval_str, dice)))
    pretty_str = arg_str % (tuple(map(_get_pretty_str, dice)))

    # Showing the actual error will hopefully give a better hint of what is
    # wrong with the syntax than a generic error message.
    try:
        result = eval_equation(eval_str)
    except Exception as e:
        bot.reply("SyntaxError, eval(%s), %s" % (eval_str, e))
        return

    bot.reply("You roll %s: %s = %d" % (
        trigger.group(2), pretty_str, result))


@sopel.module.commands("choice")
@sopel.module.commands("ch")
@sopel.module.commands("choose")
@sopel.module.priority("medium")
def choose(bot, trigger):
    """
    .choice option1|option2|option3 - Makes a difficult choice easy.
    """
    if not trigger.group(2):
        return bot.reply('I\'d choose an option, but you didn\'t give me any.')
    choices = [trigger.group(2)]
    for delim in '|\\/,':
        choices = trigger.group(2).split(delim)
        if len(choices) > 1:
            break
    # Use a different delimiter in the output, to prevent ambiguity.
    for show_delim in ',|/\\':
        if show_delim not in trigger.group(2):
            show_delim += ' '
            break

    pick = random.choice(choices)
    return bot.reply('Your options: %s. My choice: %s' % (show_delim.join(choices), pick))


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)

@sopel.module.commands("ex")
@sopel.module.priority("medium")
@sopel.module.example(".ex 3", 'You roll [3, 6, 7]: 1 Success') #Basic
@sopel.module.example(".ex 3 d0", 'You roll [3, 6, 10]: 1 Successes') #No Doubles
@sopel.module.example(".ex 3 d7", 'You roll [3, 6, 7]: 2 Successes') #Double 7s
@sopel.module.example(".ex 3 t4", 'Target 4: You roll [1, 4, 5]: 2 Successes') #Target number is 4

def exRoll(bot, trigger):
    dice_regexp = r"\d*"
    op_regexp = r"[dert+-]\d*"
    if not trigger.group(2):
        return bot.reply("No dice to roll.")
    arg_str = trigger.group(2)

    dice_match = re.match(dice_regexp, arg_str)
    if not dice_match:
        return bot.reply("No dice to roll.")

    dice_num = int(dice_match.group(0))

    target = 7
    double = 10
    extra_successes = 0
    exploding = []
    reroll = []

    operations = re.findall(op_regexp, arg_str)
    #this should be a lambda
    for operation in operations:
        value = operation[1:]
        if operation[0] == 't':
            target = int(value);
        if operation[0] == 'd':
            double = int(value)
        if operation[0] == '+' and reroll.count(value) == 0:
            extra_successes += int(value)
        if operation[0] == '-' and reroll.count(value) == 0:
            extra_successes -= int(value)

    pouch = DicePouch(dice_num, 10, extra_successes)
    result = arg_str+": "+pouch.get_storyteller_result_string(target, double)
    return bot.reply(result)