znc-slackonmsg
=============

ZNC python module to me when messaged when away. A bit
too much of this is hardcoded at the moment, but should be easy
for people to use as a basis of their own solutions.

The theory is simple, on a privmsg, or when your nick is said
in channel, send you an notification on slack if you are currently away.
This lets you know people are looking for you, and maybe even
pop on IRC from your mobile platform.


Requirements
=============
* znc irc proxy >= 1.0 built with python support


Installation
=============
Download this repo.

Copy slackonmsg.py to your znc plugins directory.

Change the relevant slack information in the file.

From within your IRC client connected through znc proxy:

   /znc loadmodule modpython

   /znc loadmodule slackonmsg

The addresses are persisted in znc's registry, so you only need
to specify them the first time the module loads, or when you want
to change their values.


Runtime
=============
A certain amount of debugging will show up on a slackonmsg privmsg
channel when running, this is normal.
