import unittest
import socket
import subprocess
import os
import time
import json

TCP_IP = 'localhost'
TCP_PORT = 5005

class TestAddFields(unittest.TestCase):
	def setUp(self):
		with open('add_fields.toml', 'w') as f:
			f.write("""
				[AddFieldsFilter]
				type = "SandboxFilter"
				message_matcher = "Type == 'add.fields'"
				[AddFieldsFilter.config]
				fields = "uuid"
				uuid = "uuid_test"
				type_output = "output"
			""")
			f.flush()
		subprocess.check_call(['heka-sbmgr', '-action=load', '-config=PlatformTest.toml', '-script=/home/helioslite/heka-hl-sandboxes/filters/add_static_fields.lua', '-scriptconfig=add_fields.toml'])
		self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.cs.connect((TCP_IP, TCP_PORT))

	def tearDown(self):
		self.cs.close()
		subprocess.check_call(['heka-sbmgr', '-action=unload', '-config=PlatformTest.toml', '-filtername=AddFieldsFilter'])
		proc.terminate() #put this command at the end of the final test
		os.remove("add_fields.toml")
		os.remove("output.log")

	def test_sandboxes(self):
		time.sleep(1)
		self.cs.send(json.dumps({'Timestamp': 10, 'Type': 'add.fields', 'Payload': 'titi', 'Fields': {'name': 'tata', 'value': 'toto'}})+'\n')
		time.sleep(1)
		fi = open('output.log', 'r')
		for line in fi:
			print line.lstrip(': |')

if __name__ == '__main__':
	proc = subprocess.Popen(['hekad', '-config', 'heka.toml'], stderr=subprocess.PIPE)
	time.sleep(1)
	suite = unittest.TestLoader().loadTestsFromTestCase(TestAddFields)
	unittest.TextTestRunner(verbosity=2).run(suite)
