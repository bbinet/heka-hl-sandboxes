import unittest
import socket
from subprocess import Popen, PIPE
from os import remove
from time import sleep

TCP_IP = 'localhost'
TCP_PORT = 5005

class TestAddFields(unittest.TestCase):
	def setUp(self):
		tomlConfig = '\n'.join(('[AddFieldsFilter]',
			'type = "SandboxFilter"',
			'message_matcher = "Type == \'add.fields\'"',
			'[AddFieldsFilter.config]',
			'fields = "uuid"',
			'uuid = "uuid_test"',
			'type_output = "output"'))
		fo = open("add_fields.toml", "w")
		fo.write(tomlConfig)
		fo.close()
		sleep(1)
		Popen(['heka-sbmgr', '-action=load', '-config=PlatformTest.toml', '-script=/home/helioslite/heka-hl-sandboxes/filters/add_static_fields.lua', '-scriptconfig=add_fields.toml'])
		self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.cs.connect((TCP_IP, TCP_PORT))

	def tearDown(self):
		self.cs.close()
		Popen(['heka-sbmgr', '-action=unload', '-config=PlatformTest.toml', '-filtername=AddFieldsFilter'])
		sleep(1)
		proc.terminate() #put this command at the end of the final test
		remove("add_fields.toml")
		remove("output.log")

	def test_sandboxes(self):
		sleep(1)
		Timestamp = "10"
		Type = "add.fields"
		Payload = "toto"
		Severity = "7"
		self.cs.send(Timestamp + ' ' + Type + ' ' + Payload + ' ' + Severity + ' |name:tata\n')
		sleep(1)
		fi = open('output.log', 'r')
		for line in fi:
			print line.lstrip(': |')

if __name__ == '__main__':
	proc = Popen(['hekad', '-config', 'heka.toml'], stderr=PIPE)
	suite = unittest.TestLoader().loadTestsFromTestCase(TestAddFields)
	unittest.TextTestRunner(verbosity=2).run(suite)
