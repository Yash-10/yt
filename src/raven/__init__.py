"""
Raven
=====

    Raven is the plotting interface, with support for several
    different engines.  Well, two for now, but maybe more later.
    Who knows?

G{packagetree}

@author: U{Matthew Turk<http://www.stanford.edu/~mturk/>}
@organization: U{KIPAC<http://www-group.slac.stanford.edu/KIPAC/>}
@contact: U{mturk@slac.stanford.edu<mailto:mturk@slac.stanford.edu>}
"""
axis_labels = [('y','z'),('x','z'),('x','y')]
axis_names = {0: 'x', 1: 'y', 2: 'z'}

vm_axis_names = {0:'x', 1:'y', 2:'z', 3:'dx', 4:'dy'}

from yt.logger import ravenLogger as mylog
from yt.config import ytcfg
from yt.arraytypes import *
import yt.lagos as lagos
try:
    import yt.raven.deliveration as deliveration
except:
    mylog.warning("Deliverator import failed; all deliverator actions will fail!")

import time, types, string, os


# We now check with ytcfg to see which backend we want

backend = ytcfg["raven","backend"]

if backend.upper()=="HD":
    import backends.HD as be
elif backend.upper()=="MPL":
    import backends.MPL as be

from PlotTypes import *
from PlotConfig import *
