import unittest
import socket
import subprocess
import os
import sys
import time
import json
import tempfile
import shutil

MAX_BYTES = 5000
HEKA_TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
HEKA_HL_DIR = os.path.realpath(os.path.join(HEKA_TESTS_DIR, '..'))
HEKA_FILTERS_DIR = os.path.join(HEKA_HL_DIR, 'filters')
HEKA_TOML = os.path.join(HEKA_TESTS_DIR, 'heka.toml')
SANBOXMGR_TOML = os.path.join(HEKA_TESTS_DIR, 'sbmgr.toml')
ENV = {
    'HEKA_HL_DIR': HEKA_HL_DIR,
    'HEKA_TESTS_DIR': HEKA_TESTS_DIR,
    'JSON_INPUT_PORT': '6010',
    'JSON_OUTPUT_PORT': '6011',
    'LOG_INPUT_PORT': '6020',
    'LOG_OUTPUT_PORT': '6021',
}

def setUpModule():
    global PROC
    ENV['TMP_DIR'] = tempfile.mkdtemp(prefix='heka-hl-')
    if '-b' in sys.argv or '--buffer' in sys.argv:
        PROC = subprocess.Popen(
            ['/usr/bin/hekad', '-config', HEKA_TOML],
            stdout=subprocess.PIPE,
            env=ENV)
    else:
        PROC = subprocess.Popen(['/usr/bin/hekad', '-config', HEKA_TOML], env=ENV)
    time.sleep(1)

def tearDownModule():
    global PROC
    PROC.terminate()
    shutil.rmtree(ENV['TMP_DIR'])


class HekaTestCase(unittest.TestCase):

    def send_json(self, msg):
        # TODO: add timeout
        print "=> %s" % json.dumps(msg)
        self.heka_output.sendto(
            json.dumps(msg) + '\n',
            ('localhost', int(ENV['JSON_OUTPUT_PORT'])))

    def receive_json(self):
        # TODO: add timeout
        data, _ = self.heka_input.recvfrom(MAX_BYTES)
        print "<= %s" % data
        return json.loads(data)

    @classmethod
    def setUpClass(self):
        self.tmpdir = tempfile.mkdtemp()
        for item in self.sandboxes:
            self.tmpconfig = os.path.join(self.tmpdir, item + '.toml')
            with open(self.tmpconfig, 'w') as f:
                f.write(self.sandboxes[item]['toml'])
                f.flush()
            subprocess.check_call([
                '/usr/bin/heka-sbmgr',
                '-action=load',
                '-config=%s' % SANBOXMGR_TOML,
                '-script=' + self.sandboxes[item]['file'],
                '-scriptconfig=' + self.tmpconfig])
        time.sleep(1)
        self.heka_output = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_input.bind(('localhost', int(ENV['JSON_INPUT_PORT'])))

    @classmethod
    def tearDownClass(self):
        for item in self.sandboxes:
            subprocess.check_call([
            '/usr/bin/heka-sbmgr',
            '-action=unload',
            '-config=%s' % SANBOXMGR_TOML,
            '-filtername=' + item])
        shutil.rmtree(self.tmpdir)
        self.heka_output.close()
        self.heka_input.close()


class TestAddFields(HekaTestCase):

    sandboxes = {'TestFilter': {
        'file': '%s/add_static_fields.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
fields = "uuid"
uuid = "uuid_test"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['uuid'], 'uuid_test', 'uuid field should be add to the current message with uuid_test value')
        self.assertEqual(data['Fields']['name'], 'name_test', 'name field should be keep the same value: "name_test"')


class TestAddModeField(HekaTestCase):

    sandboxes = {'TestFilter': {
        'file': '%s/add_mode_field.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
type_output = "output"
"""}}

    def test_sandbox(self):
        # send message from tracker01_roll_angle before the first mode message
        # equivalent to a message without tracker attachment
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_json()
        self.assertFalse('mode' in data['Fields'], 'mode field should not be present since no previous message has been sent with a mode name')

        # send message with mode: 0
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 0
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['mode'], 0, 'mode should be set to 0 with the current message which is a mode metric set to 0')

        # send first message from tracker01_roll_angle
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['mode'], 0, 'mode should be set to 0 when a previous message with mode 0 has been sent before')

        # send first message from tracker02_roll_angle
        # we should don't have any impact by the change mode of tracker 01
        # which should be unstage
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker02_roll_angle',
                'value': 15
                }
            })
        data = self.receive_json()
        self.assertFalse('mode' in data['Fields'], 'mode field should not be present since no previous message has been sent with a mode name')

        # send message with mode: 2
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_mode',
                'value': 2
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['mode'], 2, 'mode should be set to 2 with the current message which is a mode metric set to 2')

        # send first message from tracker01_roll_angle
        # and test if other fields are untouched
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'trserver_tracker01_roll_angle',
                'value': 15
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['mode'], 2, 'mode should be set to 2 when a previous message with mode 2 has been sent before')
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_roll_angle', 'name field should be keep the same value: "trserver_tracker01_roll_angle"')
        self.assertEqual(data['Fields']['value'], 15, 'value field should be keep the same value: 15')


class TestRegexDispatchMetric(HekaTestCase):

    sandboxes = {'TestFilter': {
        'file': '%s/regex_dispatch_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestFilter.config]
matchers = "windMetric allMetric"
windMetric_regex = "wind.*"
windMetric_type_output = "output.wind"
allMetric_regex = ".*"
allMetric_type_output = "output.all"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'wind_test',
                'value': 10
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name'], 'wind_test', 'name field should be keep the same value: "wind_test"')
        self.assertEqual(data['Fields']['value'], 10, 'value field should be keep the same value: 10')
        self.assertEqual(data['Type'], 'heka.sandbox.output.wind', 'Type field should be: "heka.sandbox.output.wind"')

        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'other_wind_test',
                'value': 12
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')

        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'other_metric',
                'value': 7
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')


class TestAggregateMetric(HekaTestCase):

    sandboxes = {'TestMaxFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestMaxFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.max'"
ticker_interval = 3
[TestMaxFilter.config]
ticker_interval = 3
aggregation = "max"
type_output = "output"
    """}, 'TestMinFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestMinFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.min'"
ticker_interval = 3
[TestMinFilter.config]
ticker_interval = 3
aggregation = "min"
type_output = "output"
    """}, 'TestCountFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestCountFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.count'"
ticker_interval = 3
[TestCountFilter.config]
ticker_interval = 3
aggregation = "count"
type_output = "output"
    """}, 'TestLastFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestLastFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.last'"
ticker_interval = 3
[TestLastFilter.config]
ticker_interval = 3
aggregation = "last"
type_output = "output"
    """}, 'TestSumFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestSumFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.sum'"
ticker_interval = 3
[TestSumFilter.config]
ticker_interval = 3
aggregation = "sum"
type_output = "output"
    """}, 'TestAvgFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestAvgFilter]
type = "SandboxFilter"
filename = "../filters/aggregate_metric.lua"
message_matcher = "Type == 'test.avg'"
ticker_interval = 3
[TestAvgFilter.config]
ticker_interval = 3
aggregation = "avg"
type_output = "output"
"""}}

    def test_sandbox_max(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.max',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.max',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.max',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 5)
        self.assertEqual(data['Fields']['name_test_2'], 3)

    def test_sandbox_min(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.min',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.min',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.min',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['name_test_2'], 3)

    def test_sandbox_count(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.count',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.count',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.count',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['name_test_2'], 1)

    def test_sandbox_last(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.last',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.last',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.last',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 5)
        self.assertEqual(data['Fields']['name_test_2'], 3)

    def test_sandbox_sum(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.sum',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 7)
        self.assertEqual(data['Fields']['name_test_2'], 3)

    def test_sandbox_avg(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.avg',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 3.5)
        self.assertEqual(data['Fields']['name_test_2'], 3)


class TestGatherLastMetric(HekaTestCase):

    sandboxes = {'TestFilter': {
        'file': '%s/gather_last_metrics.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
ticker_interval = 2
[TestFilter.config]
type_output = "output"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_1',
                'value': 10
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_2',
                'value': 12
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test_3',
                'value': 7
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name_test_1'], 10, 'name_test_1 field should be set to: 10')
        self.assertEqual(data['Fields']['name_test_2'], 12, 'name_test_2 field should be set to: 12')
        self.assertEqual(data['Fields']['name_test_3'], 7, 'name_test_3 field should be set to: 7')


class TestFormatMetricName(HekaTestCase):

    sandboxes = {
        'TestAddFields': {
            'file': '%s/add_static_fields.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestAddFields]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
[TestAddFields.config]
type_output = "encode.influxdb"
fields = "uuid"
uuid = "uuid_test"
"""},
        'TestGatherFields': {
            'file': '%s/format_metric_name.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestGatherFields]
type = "SandboxFilter"
message_matcher = "Type == 'heka.sandbox.encode.influxdb'"
[TestGatherFields.config]
fields = "uuid name value"
separator = "-"
type_output = "output"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Payload': 'payload_test',
            'Fields': {
                'name': 'name_test',
                'value': 10
                }
            })
        data = self.receive_json()
        self.assertEqual(data['Fields']['name'], 'uuid_test-name_test-10', 'name field should be set to: uuid_test-name_test-10')


class TestLogData(HekaTestCase):

    def setUp(self):
        self.heka_log_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_log_input.bind(('localhost', int(ENV['LOG_INPUT_PORT'])))

    def tearDown(self):
        self.heka_log_input.close()

    sandboxes = {
        'TestDecodeLogMetric': {
            'file': '%s/decode_metric.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestDecodeLogMetric]
type = "SandboxFilter"
message_matcher = "Type == 'log.input' && Fields[decoder_type] == 'metric'"
[TestDecodeLogMetric.config]
type_output = "encode.log.metric"
"""},
        'TestEncodeLogMetric': {
            'file': '%s/encode_metric.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestEncodeLogMetric]
type = "SandboxFilter"
message_matcher = "Type == 'heka.sandbox.encode.log.metric'"
    [TestEncodeLogMetric.config]
    type_output = "log.output"
"""},
        'TestDecodeLogEvent': {
            'file': '%s/decode_event.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestDecodeLogEvent]
type = "SandboxFilter"
message_matcher = "Type == 'log.input' && Fields[decoder_type] == 'event'"
[TestDecodeLogEvent.config]
type_output = "encode.log.event"
"""},
        'TestEncodeLogEvent': {
            'file': '%s/encode_event.lua' % HEKA_FILTERS_DIR,
            'toml': """
[TestEncodeLogEvent]
type = "SandboxFilter"
message_matcher = "Type == 'heka.sandbox.encode.log.event'"
    [TestEncodeLogEvent.config]
    type_output = "log.output"
"""}}

    def send_log(self, msg):
        self.heka_output.sendto(
            msg, ('localhost', int(ENV['LOG_OUTPUT_PORT'])))

    def receive_log(self):
        data, _ = self.heka_log_input.recvfrom(MAX_BYTES)
        return data

    def test_sandbox_metric(self):
        msg = '[14:03:41 hl-mc-1-dev d539a1ab-1742-43c5-982e-02fab58283fa 1422453821076360704 7 metric:0] trserver_tracker01_roll_angle 86.27218\n'
        self.send_log(msg)
        data = self.receive_log()
        self.assertEqual(data, msg)

    def test_sandbox_event(self):
        msg = '[14:03:41 hl-mc-1-dev d539a1ab-1742-43c5-982e-02fab58283fa 1422453821076360704 2 event:0] "test message with \'some\' \\"quotes\\" and \\n cr"\n'
        self.send_log(msg)
        data = self.receive_log()
        self.assertEqual(data, msg)


if __name__ == '__main__':
    unittest.main()
