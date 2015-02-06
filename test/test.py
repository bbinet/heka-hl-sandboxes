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

    def send_msg(self, msg):
        self.heka_output.sendto(json.dumps(msg)+'\n', (HEKA_IP, HEKA_OUTPUT_PORT))

    def receive_msg(self):
        data, _ = self.heka_input.recvfrom(5000)
        return data

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
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertEqual(data['Fields']['uuid'], 'uuid_test')
        self.assertEqual(data['Fields']['name'], 'name_test')


class TestAddModeField(HekaTestCase):

    sandbox = '../filters/add_mode_field.lua'
    unload_sandboxes = ['TestFilter']
    config = """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
"""

    def test_sandbox(self):
        # send message from tracker01_roll_angle before the first mode message
        # equivalent to a message without tracker attachment
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertFalse('mode' in data['Fields'])

        # send message with mode: 0
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 0
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertEqual(data['Fields']['mode'], 0)

        # send first message from tracker01_roll_angle
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertEqual(data['Fields']['mode'], 0)

        # send first message from tracker02_roll_angle
        # we should don't have any impact by the change mode of tracker 01
        # which should be unstage
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker02_roll_angle',
                'value': 15
                }
            })
        data = HekaTestCase.receive_msg(self)
        data = json.loads(data)
        self.assertFalse('mode' in data['Fields'])

        # send message with mode: 2
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 2
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertEqual(data['Fields']['mode'], 2)

        # send first message from tracker01_roll_angle
        # and test if other fields are untouched
        HekaTestCase.send_msg(self, {
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = json.loads(HekaTestCase.receive_msg(self))
        self.assertEqual(data['Fields']['mode'], 2)
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_roll_angle')
        self.assertEqual(data['Fields']['value'], 15)


if __name__ == '__main__':
    unittest.main()
