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
        for key in self.sandboxes:
            self.tmpconfig = os.path.join(self.tmpdir, key + '.toml')
            with open(self.tmpconfig, 'w') as f:
                f.write(self.sandboxes[key])
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
        for key in self.sandboxes:
            subprocess.check_call([
            'heka-sbmgr',
            '-action=unload',
            '-config=PlatformTest.toml',
            '-filtername=' + key])
        shutil.rmtree(self.tmpdir)
        self.heka_output.close()
        self.heka_input.close()


class TestAddFields(HekaTestCase):

    sandbox = '../filters/add_static_fields.lua'
    sandboxes = {'TestFilter': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
fields = "uuid"
uuid = "uuid_test"
"""}

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
    sandboxes = {'TestFilter': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
"""}

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
    sandboxes = {'TestFilter': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
matchers = "windMetric allMetric"
windMetric_regex = "wind.*"
windMetric_type_output = "output.wind"
allMetric_regex = ".*"
allMetric_type_output = "output.all"
"""}

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


class TestAggregatehMetric(HekaTestCase):

    sandbox = '../filters/aggregate_metric.lua'
    sandboxes = {'TestMaxFilter': """
[TestMaxFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.max'"
ticker_interval = 3
[TestMaxFilter.config]
aggregation = "max"
type_output = "output"
    """, 'TestMinFilter': """
[TestMinFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.min'"
ticker_interval = 3
[TestMinFilter.config]
aggregation = "min"
type_output = "output"
    """, 'TestCountFilter': """
[TestCountFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.count'"
ticker_interval = 3
[TestCountFilter.config]
aggregation = "count"
type_output = "output"
    """, 'TestLastFilter': """
[TestLastFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.last'"
ticker_interval = 3
[TestLastFilter.config]
aggregation = "last"
type_output = "output"
    """, 'TestSumFilter': """
[TestSumFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.sum'"
ticker_interval = 3
[TestSumFilter.config]
aggregation = "sum"
type_output = "output"
    """, 'TestAvgFilter': """
[TestAvgFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.avg'"
ticker_interval = 3
[TestAvgFilter.config]
aggregation = "avg"
type_output = "output"
"""}

    def test_sandbox_max(self):

        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.max',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.max',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.max',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.max',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 5, 'value field should be with "max" aggregation: 5')

    def test_sandbox_min(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.min',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.min',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.min',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.min',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 3
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 1, 'value field should be with "min" aggregation: 1')

    def test_sandbox_count(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.count',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.count',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.count',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.count',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 3
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 4, 'value field should be with "count" aggregation: 4')

    def test_sandbox_last(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.last',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.last',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.last',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.last',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 3
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 3, 'value field should be with "last" aggregation: 3')

    def test_sandbox_sum(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 3
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 11, 'value field should be with "sum" aggregation: 11')

    def test_sandbox_avg(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 1
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 2
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 5
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 3
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['value'], 2.75, 'value field should be with "avg" aggregation: 2.75')


class TestGatherLastMetric(HekaTestCase):

    sandbox = '../filters/gather_last_metrics.lua'
    sandboxes = {'TestFilter': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
ticker_interval = 2
[TestFilter.config]
type_output = "output"
"""}

    def test_sandbox(self):
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_1',
                'value': 10
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_2',
                'value': 12
                }
            })
        self.send_msg({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_3',
                'value': 7
                }
            })
        data = self.receive_msg()
        self.assertEqual(data['Fields']['name_test_1'], 10, 'name_test_1 field should be set to: 10')
        self.assertEqual(data['Fields']['name_test_2'], 12, 'name_test_2 field should be set to: 12')
        self.assertEqual(data['Fields']['name_test_3'], 7, 'name_test_3 field should be set to: 7')


if __name__ == '__main__':
    unittest.main()
