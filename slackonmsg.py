#  Copyright 2013 Sean Dague <sean@dague.net>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pprint
import sys
import traceback
import requests
import json

import znc

# Slack connection information
SLACK_CHANNEL = '@dims'
SLACK_USER_NAME = 'zncbot'
SLACK_EMOJI = ':ghost:'
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/XYZ/123'

pp = pprint.PrettyPrinter()


def _is_self(*args):
    """Utility method to make sure only calling on right modules."""
    if len(args) > 1 and type(args[0]) == slackonmsg:
        return args[0]
    return None


def trace(fn):
    """Useful decorator for debugging."""

    def wrapper(*args, **kwargs):
        s = _is_self(*args)
        if s:
            s.PutModule("TRACE: %s" % (fn.__name__))
        return fn(*args, **kwargs)

    return wrapper


def catchfail(fn):
    """Catch exceptions and get them onto the module channel."""

    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            s = _is_self(*args)
            if s:
                s.PutModule("Failed with %s" % (e))
                # then get the whole stack trace out
                lines = traceback.format_exception(exc_type, exc_value,
                                                   exc_traceback)
                for line in lines:
                    s.PutModule(line)

    return wrapper


class slackonmsgtimer(znc.Timer):
    nick = None
    chan = None
    mod = None

    def RunJob(self):
        if self.mod.send_notification(self.nick, self.chan):
            self.mod.PutModule("clearing buffer")
            self.mod.clear_buffer(self.nick, self.chan)
            self.mod.PutModule("Notification sent")


class slackonmsg(znc.Module):
    """Module to send slack notifications to users when they are away.

    After moving from maiu to znc, the one feature I missed was the
    email when away. This tries to replicate this feature through emailing
    highlights as well as privmsg to a predefined email account.
    """
    # module_types = [znc.CModInfo.UserModule]

    description = 'send slack notification on message'

    keywords = []
    pending = {}

    def _should_send(self, nick, chan=None, msg=""):
        """Conditions on which we should send a notification."""
        if not self.GetNetwork().IsIRCAway():
            return False
        else:
            return True

    def _highlight(self, msg):
        if msg.find(self.GetNetwork().GetCurNick()) != -1:
            return True

        for word in self.keywords:
            if msg.find(word) != -1:
                return True

        return False

    def buffer(self, nick, chan):
        key = "%s:%s" % (nick, chan)
        if key in self.pending:
            return self.pending[key]
        else:
            return None

    def create_buffer(self, nick, chan):
        self.pending["%s:%s" % (nick, chan)] = ""

    def clear_buffer(self, nick, chan):
        key = "%s:%s" % (nick, chan)
        del self.pending[key]

    def add_to_buffer(self, nick, chan, msg):
        key = "%s:%s" % (nick, chan)
        cur = self.pending[key]
        self.pending[key] = cur + "\n" + msg

    @catchfail
    def send(self, nick, chan=None, msg=""):
        if not self._should_send(nick=nick, chan=chan, msg=msg):
            return False

        if self.buffer(nick, chan) is None:
            self.create_buffer(nick, chan)
            timer = self.CreateTimer(slackonmsgtimer, interval=5, cycles=1)
            timer.mod = self
            timer.nick = nick
            timer.chan = chan

        self.add_to_buffer(nick, chan, msg)

    @catchfail
    def send_notification(self, nick, chan):
        msg = self.buffer(nick, chan)
        if not msg:
            self.PutModule("Something is wrong, no message")
            return False

        if chan:
            text = 'IRC message on %s from %s : %s' % (chan, nick, msg)
        else:
            text = 'IRC priv message from %s : %s' % (nick, msg)

        data = {
            'channel': SLACK_CHANNEL,
            'username': SLACK_USER_NAME,
            'icon_emoji': SLACK_EMOJI,
            'text': text
        }

        requests.post(SLACK_WEBHOOK_URL, data={'payload': json.dumps(data)})
        return True

    @catchfail
    @trace
    def OnStatusCommand(self, cmd):
        print("STATUS: %s" % cmd)
        return znc.CONTINUE

    def OnLoad(self, args, msg):
        self.keywords = [
            self.GetUser().GetNick()
        ]

        self.PutModule("slackonmsg loaded successfully")
        self.PutModule("notifications will be sent to channel '%s', "
                       "from user '%s'" %
                       (SLACK_CHANNEL, SLACK_USER_NAME))
        return znc.CONTINUE

    @catchfail
    def OnPrivMsg(self, nick, msg):
        self.send(nick=nick.GetNick(), msg=msg.s)
        return znc.CONTINUE

    @catchfail
    def OnChanMsg(self, nick, channel, msg):
        if self._highlight(msg.s):
            self.send(nick=nick.GetNick(), chan=channel.GetName(),
                      msg=msg.s)
        return znc.CONTINUE

    @catchfail
    def GetWebMenuTitle(self):
        return "Post to Slack on messages when away"
