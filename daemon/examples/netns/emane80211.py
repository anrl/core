#!/usr/bin/python -i

# Copyright (c)2010-2014 the Boeing Company.
# See the LICENSE file included in this distribution.

# Example CORE Python script that attaches N nodes to an EMANE 802.11abg
# network. One of the parameters is changed, the pathloss mode.

import datetime
import optparse
import sys

from core import constants
from core.emane.ieee80211abg import EmaneIeee80211abgModel
from core.emane.nodes import EmaneNode
from core.misc import ipaddress, nodeutils, nodemaps
from core.netns import nodes

# node list (count from 1)
from core.session import Session

n = [None]


def main():
    usagestr = "usage: %prog [-h] [options] [args]"
    parser = optparse.OptionParser(usage=usagestr)
    parser.set_defaults(numnodes=5)

    parser.add_option("-n", "--numnodes", dest="numnodes", type=int,
                      help="number of nodes")

    def usage(msg=None, err=0):
        sys.stdout.write("\n")
        if msg:
            sys.stdout.write(msg + "\n\n")
        parser.print_help()
        sys.exit(err)

    # parse command line options
    (options, args) = parser.parse_args()

    if options.numnodes < 1:
        usage("invalid number of nodes: %s" % options.numnodes)

    for a in args:
        sys.stderr.write("ignoring command line argument: '%s'\n" % a)

    start = datetime.datetime.now()

    # IP subnet
    prefix = ipaddress.Ipv4Prefix("10.83.0.0/16")
    # session with some EMANE initialization
    cfg = {'verbose': 'false'}
    session = Session(1, config=cfg, persistent=True)
    session.master = True
    session.location.setrefgeo(47.57917, -122.13232, 2.00000)
    session.location.refscale = 150.0
    session.config['emane_models'] = "RfPipe, Ieee80211abg, Bypass"
    session.emane.loadmodels()
    if 'server' in globals():
        server.addsession(session)

    # EMANE WLAN
    print "creating EMANE WLAN wlan1"
    wlan = session.add_object(cls=EmaneNode, name="wlan1")
    wlan.setposition(x=80, y=50)
    names = EmaneIeee80211abgModel.getnames()
    values = list(EmaneIeee80211abgModel.getdefaultvalues())
    # TODO: change any of the EMANE 802.11 parameter values here
    for i in range(0, len(names)):
        print "EMANE 80211 \"%s\" = \"%s\"" % (names[i], values[i])
    try:
        values[names.index('pathlossmode')] = '2ray'
    except ValueError:
        values[names.index('propagationmodel')] = '2ray'

    session.emane.setconfig(wlan.objid, EmaneIeee80211abgModel.name, values)
    services_str = "zebra|OSPFv3MDR|IPForward"

    print "creating %d nodes with addresses from %s" % \
          (options.numnodes, prefix)
    for i in xrange(1, options.numnodes + 1):
        tmp = session.add_object(cls=nodes.CoreNode, name="n%d" % i,
                                 objid=i)
        tmp.newnetif(wlan, ["%s/%s" % (prefix.addr(i), prefix.prefixlen)])
        tmp.cmd([constants.SYSCTL_BIN, "net.ipv4.icmp_echo_ignore_broadcasts=0"])
        tmp.setposition(x=150 * i, y=150)
        session.services.addservicestonode(tmp, "", services_str)
        n.append(tmp)

    # this starts EMANE, etc.
    session.node_count = str(options.numnodes + 1)
    session.instantiate()

    # start a shell on node 1
    n[1].term("bash")

    print "elapsed time: %s" % (datetime.datetime.now() - start)


if __name__ == "__main__" or __name__ == "__builtin__":
    # configure nodes to use
    node_map = nodemaps.NODES
    nodeutils.set_node_map(node_map)

    main()
