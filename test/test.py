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
        return json.loads(data)

    @classmethod
    def setUpClass(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpconfig = os.path.join(self.tmpdir, 'config.toml')
        with open(self.tmpconfig, 'w') as f:
            f.write(self.config)
            f.flush()
        subprocess.check_call([
            'heka-sbmgr',
            '-action=load',
            '-config=PlatformTest.toml',
            '-script=' + self.sandbox,
            '-scriptconfig=' + self.tmpconfig])
        time.sleep(1)
        self.heka_output = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input.bind((HEKA_IP, HEKA_INPUT_PORT))

    @classmethod
    def tearDownClass(self):
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
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['uuid'], 'uuid_test', 'uuid field should be add to the current message with uuid_test value')
        self.assertEqual(data['Fields']['name'], 'name_test', 'name field should be keep the same value: "name_test"')


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
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_msg()
        self.assertFalse('mode' in data['Fields'], 'mode field should not be present since no previous message has been sent with a mode name')

        # send message with mode: 0
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 0
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['mode'], 0, 'mode should be set to 0 with the current message which is a mode metric set to 0')

        # send first message from tracker01_roll_angle
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['mode'], 0, 'mode should be set to 0 when a previous message with mode 0 has been sent before')

        # send first message from tracker02_roll_angle
        # we should don't have any impact by the change mode of tracker 01
        # which should be unstage
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker02_roll_angle',
                'value': 15
                }
            })
        data = self.receive_msg()
        self.assertFalse('mode' in data['Fields'], 'mode field should not be present since no previous message has been sent with a mode name')

        # send message with mode: 2
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 2
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['mode'], 2, 'mode should be set to 2 with the current message which is a mode metric set to 2')

        # send first message from tracker01_roll_angle
        # and test if other fields are untouched
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['mode'], 2, 'mode should be set to 2 when a previous message with mode 2 has been sent before')
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_roll_angle', 'name field should be keep the same value: "trserver_tracker01_roll_angle"')
        self.assertEqual(data['Fields']['value'], 15, 'value field should be keep the same value: 15')


class TestRegexDispatchMetric(HekaTestCase):

    sandbox = '../filters/regex_dispatch_metric.lua'
    unload_sandboxes = ['TestFilter']
    config = """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
matchers = "windMetric allMetric"
windMetric_regex = "wind.*"
windMetric_type_output = "output.wind"
allMetric_regex = ".*"
allMetric_type_output = "output.all"
"""

    def test_sandbox(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'wind_test',
                'value': 10
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['name'], 'wind_test', 'name field should be keep the same value: "wind_test"')
        self.assertEqual(data['Fields']['value'], 10, 'value field should be keep the same value: 10')
        self.assertEqual(data['Type'], 'heka.sandbox.output.wind', 'Type field should be: "heka.sandbox.output.wind"')

        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'other_wind_test',
                'value': 12
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')

        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'other_metric',
                'value': 7
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')


if __name__ == '__main__':
    unittest.main()
