import unittest
import socket
import subprocess
import os
import time
import json
import tempfile
import shutil

TCP_IP = 'localhost'
TCP_PORT = 5005

def setUpModule():
	global PROC
	global TEMP_DIR
	global SOCKET_S
	global SOCKET_R
	global RECEIPT

	TEMP_DIR = tempfile.mkdtemp()
	PROC = subprocess.Popen(['hekad', '-config', 'heka.toml'], stderr=subprocess.PIPE)
	time.sleep(1)
	SOCKET_S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	SOCKET_S.connect((TCP_IP, TCP_PORT))
	SOCKET_R = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	SOCKET_R.bind((TCP_IP, 5007))
	SOCKET_R.listen(1)
	RECEIPT, _ = SOCKET_R.accept()

def tearDownModule():
	global PROC
	global TEMP_DIR
	global SOCKET_S
	global RECEIPT

	SOCKET_S.close()
	RECEIPT.close()
	PROC.terminate()
	shutil.rmtree(TEMP_DIR)

class TestAddFields(unittest.TestCase):
	def setUp(self):
		global TEMP_DIR
		with open(TEMP_DIR + '/add_fields.toml', 'w') as f:
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
		subprocess.check_call(['heka-sbmgr', '-action=load', '-config=PlatformTest.toml', '-script=' + os.path.abspath('..') + '/filters/add_static_fields.lua', '-scriptconfig=' + TEMP_DIR + '/add_fields.toml'])

	def tearDown(self):
		subprocess.check_call(['heka-sbmgr', '-action=unload', '-config=PlatformTest.toml', '-filtername=AddFieldsFilter'])

	def test_sandbox(self):
		global SOCKET_S
		global RECEIPT

		SOCKET_S.send(json.dumps({'Timestamp': 10, 'Type': 'add.fields', 'Payload': 'titi', 'Fields': {'name': 'tata', 'value': 'toto'}})+'\n')
		data = json.loads(RECEIPT.recv(5000))
		self.assertEqual(data['Fields']['uuid'], 'uuid_test')

if __name__ == '__main__':
	unittest.main()
