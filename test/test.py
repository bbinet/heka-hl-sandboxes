import unittest
import socket
import subprocess
import os
import time
import json
import tempfile
import shutil

HEKA_IP = 'localhost'
HEKA_INPUT_PORT = 5007
HEKA_OUTPUT_PORT = 5005

def setUpModule():
    global PROC
    PROC = subprocess.Popen(['hekad', '-config', 'heka.toml'], stderr=subprocess.PIPE)
    time.sleep(1)

def tearDownModule():
    global PROC
    PROC.terminate()


class HekaTestCase(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpconfig = os.path.join(self.tmpdir, 'config.toml')
        with open(self.tmpconfig, 'w') as f:
            f.write(self.config)
            f.flush()
        subprocess.check_call([
            'heka-sbmgr',
            '-action=load',
            '-config=PlatformTest.toml',
            '-script=' + os.path.abspath(self.sandbox),
            '-scriptconfig=' + self.tmpconfig])
        time.sleep(1)
        self.heka_output = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input.bind((HEKA_IP, HEKA_INPUT_PORT))

    def tearDown(self):
        for u in self.unload_sandboxes:
            subprocess.check_call([
            'heka-sbmgr',
            '-action=unload',
            '-config=PlatformTest.toml',
            '-filtername=' + u])
        shutil.rmtree(self.tmpdir)
        self.heka_output.close()
        self.heka_input.close()


class TestAddFields(HekaTestCase):

    sandbox = '../filters/add_static_fields.lua'
    unload_sandboxes = ['TestFilter']
    config = """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
fields = "uuid"
uuid = "uuid_test"
"""

    def test_sandbox(self):
        self.heka_output.sendto(json.dumps({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                }
            })+'\n', (HEKA_IP, HEKA_OUTPUT_PORT))
        data, _ = self.heka_input.recvfrom(5000)
        data = json.loads(data)
        self.assertEqual(data['Fields']['uuid'], 'uuid_test')
        self.assertEqual(data['Fields']['name'], 'name_test')

if __name__ == '__main__':
    unittest.main()
