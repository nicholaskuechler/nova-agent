from __future__ import print_function, absolute_import
import os

from novaagent import utils
from novaagent.common.password import PasswordCommands
from subprocess import Popen, PIPE

from novaagent.libs import DefaultOS

class ServerOS(DefaultOS):
    def _setup_hostname(self, hostname):
        with open('/etc/rc.conf.local', 'a') as iffile:
            print('hostname={0}'.format(hostname), file=iffile)

    def _setup_interface(self, ifname, iface):
        with open('/etc/rc.conf.local', 'a') as iffile:
            print('# Label {0}'.format(iface['label']), file=iffile)
            for num, info in enumerate(iface['ips']):
                print('ifconfig_{0}_alias{1}="{2} netmask {3} up"'.format(ifname, num, info['ip'], info['netmask']), file=iffile)
                n = num + 1
            if 'ip6s' in iface:
                for num, info in enumerate(iface['ip6s']):
                    print('ifconfig_{0}_alias{1}="inet6 {2} netmask {3} up"'.format(ifname, n + num, info['ip'], info['netmask']), file=iffile)
                print('ipv6_enable="YES"', file=iffile)
                print('ipv6_network_interfaces="{0}"'.format(ifname), file=iffile)
            if 'gateway' in iface and iface['gateway']:
                print('defaultrouter="{0}"'.format(iface['gateway']), file=iffile)
            if 'gateway_v6' in iface and iface['gateway_v6']:
                print('ipv6_defaultrouter="{0}%{1}"'.format(iface['gateway_v6'], ifname), file=iffile)
            if 'routes' in iface:
                lans = []
                for num, route in enumerate(iface['routes']):
                    print('route_lan{0}="-net {route} -netmask {netmask} {gateway}"'.format(num, **route), file=iffile)
                    lans.append('lan{0}'.format(num))
                print('static_routes="{0}"'.format(' '.join(lans)), file=iffile)

    def resetnetwork(self, name, value):
        if os.path.exists('/etc/rc.conf.local'):
            os.rename('/etc/rc.conf.local', '/etc/rc.conf.local.bak')
        ifaces = {}
        xen_macs = utils.list_xenstore_macaddrs()
        for iface in utils.list_hw_interfaces():
            mac = utils.get_hw_addr(iface)
            if not mac or mac not in xen_macs:
                continue
            ifaces[iface] = utils.get_interface(mac)

        # set hostname
        hostname = utils.get_hostname()
        p = Popen(['hostname', hostname], stdout=PIPE, stdin=PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            return str(p.returncode)
        self._setup_hostname(hostname)

        # setup interface files
        for ifname, iface in ifaces.items():
            self._setup_interface(ifname, iface)
        return '0'
        p = Popen(['service', 'netif', 'restart'], stdout=PIPE, stdin=PIPE)
        p = Popen(['service', 'routing', 'restart'], stdout=PIPE, stdin=PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            return str(p.returncode)

        return '0'


if __name__ == '__main__':
    main()