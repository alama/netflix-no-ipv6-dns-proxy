#!/usr/local/bin/python

OPTIONS = {
    # Port to bind to.
    'listen-port': 53,

    # Address to bind to.  '::' will bind IPv6; make sure bindv6only is 0 in
    # your sysctl configuration for this binding to service IPv4 clients, too.
    # ("cat /proc/sys/net/ipv6/bindv6only" to verify.)
    'listen-address4': '192.168.1.200',
    'listen-address6': '2001:470:1996::200',

    # Here is where you configure what DNS server to proxy to.  You must
    # specify exactly one of the following options; comment out the other.

    # Specify one or more servers to proxy to.  Note that Twisted may not be
    # happy if you use an IPv6 address.
    'upstream-dns': [('127.0.0.1', 5553)],

    # Specify a resolv.conf file from which to read upstream nameservers.  As
    # noted above, if you have any upstream IPv6 servers, Twisted may not be
    # happy about that.
    # 'resolv-conf': '/etc/resolv.conf',
}

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server

class BlockNetflixAAAAResolver(object):
    def __shouldBlock(self, query):
        domainParts = query.name.name and query.name.name.split('.')

        if not domainParts or len(domainParts) < 2:
            return False

        return query.type == dns.AAAA and domainParts[-2] in ('netflix', 'nflximg')

    def query(self, query, timeout=None):
        if self.__shouldBlock(query):
            return defer.succeed(([], [], []))
        else:
            return defer.fail(error.DomainError())

def main():
    factory = server.DNSServerFactory(
        clients=[
            BlockNetflixAAAAResolver(),
            client.Resolver(
                servers=OPTIONS.get('upstream-dns', None),
                resolv=OPTIONS.get('resolv-conf', None)
            )
        ]
    )

    protocol4 = dns.DNSDatagramProtocol(controller=factory)
    protocol6 = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(OPTIONS['listen-port'], protocol4, interface=OPTIONS['listen-address4'])
    reactor.listenUDP(OPTIONS['listen-port'], protocol6, interface=OPTIONS['listen-address6'])
    reactor.listenTCP(OPTIONS['listen-port'], factory, interface=OPTIONS['listen-address4'])
    reactor.listenTCP(OPTIONS['listen-port'], factory, interface=OPTIONS['listen-address6'])

    reactor.run()

if __name__ == '__main__':
    raise SystemExit(main())
