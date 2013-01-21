#!/usr/bin/env python
# coding: utf-8
import socket, socketserver, netaddr, os, logging

config = {
	'bind': '::',
	'logging': logging.DEBUG,
	'data-dirs': {
		'person': '../person',
		'aut-num': '../aut-num',
		'inetnum': '../inetnum',
		'route': '../route'
	}
}

class TCPv6Server(socketserver.TCPServer):
	address_family = socket.AF_INET6
	allow_reuse_address = True

class GeheimWhoisDealer(socketserver.BaseRequestHandler):
	def setup(self):
		self.logger = logging.getLogger(__name__)

		self.request.send(b"% This is the GeheimVPN registry query service.\n")
		self.request.send(b"% Find out the details about this network in our wiki:\n")
		self.request.send(b"% https://wiki.geheimorganisation.org/index.php/GeheimVPN\n\n")

	def handle(self):
		data = self.request.recv(1024)
		self.request.send(self.dealWithRequest(data))
		self.request.send(b"\n% Saenk ju for traevelling wis Deutsche Bahn.")

	def dealWithRequest(self, data):
		out = ''
		success = False
		data = data.decode('utf-8').replace("\r\n", "")
		self.logger.debug(data)

		# check for IP
		if netaddr.valid_ipv4(data) or netaddr.valid_ipv6(data):
			self.logger.debug('Is IP-Address!')

			ip = netaddr.IPAddress(data)
			for net in os.listdir(config['data-dirs']['inetnum']):
				if ip in netaddr.IPNetwork(net.replace('_', '/')):
					net = self.getIpNetwork(net)
					if net:
						out = net
						success = True

		# check for ip network
		elif '/' in data and netaddr.valid_ipv4(data.split('/')[0]) or netaddr.valid_ipv6(data.split('/')[0]):
			self.logger.debug('Is IP-Network!')

			net = self.getIpNetwork(data.replace('/', '_'))
			if net:
				out = net
				success = True

		# check for ASN
		elif data[:2] == 'AS':
			self.logger.debug('Is ASN!')

			try:
				path = "{0}/{1}".format(
					config['data-dirs']['aut-num'],
					data
				)
				out += "% Information related to '{0}' \n\n".format(
					path
				)
				out += open(path, 'r').read()
				success = True
			except:
				pass

		# check for person
		else:
			self.logger.debug('Maybe a person!')

			try:
				path = "{0}/{1}".format(
					config['data-dirs']['person'],
					data
				)
				out += "% Information related to '{0}' \n\n".format(
					path
				)
				out += open(path, 'r').read()
				success = True
			except:
				pass

		if not success:
			out += "% No match found for '{0}'\n".format(
				str(data)
			)


		return bytes(out, 'UTF-8')

	def getIpNetwork(self, net):
		out = ''
		try:
			# the ip network itself
			path = "{0}/{1}".format(
				config['data-dirs']['inetnum'],
				net
			)
			out += "% Information related to '{0}' \n\n".format(
				path
			)
			out += open(path, 'r').read()

			# the route
			try:
				path = "{0}/{1}".format(
					config['data-dirs']['route'],
					net
				)
				out += "\n% Information related to '{0}' \n\n".format(
					path
				)
				out += open(path, 'r').read()
			except:
				pass
		except:
			return False

		return out

if __name__ == "__main__":
	logging.basicConfig(level=config['logging'])
	s = TCPv6Server((config['bind'], 43), GeheimWhoisDealer)
	s.serve_forever()