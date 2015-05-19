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
HEKA_OLD_FILTERS_DIR = os.path.join(HEKA_HL_DIR, 'old', 'filters')
HEKA_TOML = os.path.join(HEKA_TESTS_DIR, 'heka.toml')
SANBOXMGR_TOML = os.path.join(HEKA_TESTS_DIR, 'sbmgr.toml')
ENV = {
    'HEKA_HL_DIR': HEKA_HL_DIR,
    'HEKA_TESTS_DIR': HEKA_TESTS_DIR,
    'JSON_INPUT_PORT': '6010',
    'JSON_OUTPUT_PORT': '6011',
    'LOG_INPUT_PORT': '6020',
    'LOG_OUTPUT_PORT': '6021',
    'CARBON_INPUT_PORT': '6030',
    'TRSERVER_OUTPUT_PORT': '6040',
}
jsondec = json.JSONDecoder()

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
        i = 0
        objs = []
        while i < len(data):
            obj, i = jsondec.raw_decode(data[0:])
            objs.append(obj)
        return objs

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
            'Fields': {
                'name': 'name_test',
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['uuid'], 'uuid_test', 'uuid field should be add to the current message with uuid_test value')
        self.assertEqual(data['Fields']['name'], 'name_test', 'name field should be keep the same value: "name_test"')


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
            'Fields': {
                'name': 'wind_test',
                'value': 10
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'wind_test', 'name field should be keep the same value: "wind_test"')
        self.assertEqual(data['Fields']['value'], 10, 'value field should be keep the same value: 10')
        self.assertEqual(data['Type'], 'heka.sandbox.output.wind', 'Type field should be: "heka.sandbox.output.wind"')

        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'other_wind_test',
                'value': 12
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')

        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'other_metric',
                'value': 7
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Type'], 'heka.sandbox.output.all', 'Type field should be: "heka.sandbox.output.output"')


class TestAggregateMetric(HekaTestCase):

    sandboxes = {'TestGustMinFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestGustMinFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test.gust.min'"
ticker_interval = 3
[TestGustMinFilter.config]
ticker_interval = 3
aggregation = "min"
gust = 2
type_output = "output"
    """}, 'TestGustMaxFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestGustMaxFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test.gust.max'"
ticker_interval = 3
[TestGustMaxFilter.config]
ticker_interval = 3
aggregation = "max"
gust = 2
type_output = "output"
    """}, 'TestMaxFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestMaxFilter]
type = "SandboxFilter"
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
message_matcher = "Type == 'test.avg'"
ticker_interval = 3
[TestAvgFilter.config]
ticker_interval = 3
aggregation = "avg"
type_output = "output"
    """}, 'TestDirectFilter': {
        'file': '%s/aggregate_metric.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestDirectFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test.no'"
ticker_interval = 3
[TestDirectFilter.config]
ticker_interval = 3
aggregation = "no"
type_output = "output"
"""}}

    def test_sandbox_gust_min(self):
        self.send_json({
            'Timestamp': 10000000000,
            'Type': 'test.gust.min',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 11500000000,
            'Type': 'test.gust.min',
            'Fields': {
                'name': 'name_test_1',
                'value': 6
                }
            })
        self.send_json({
            'Timestamp': 13000000000,
            'Type': 'test.gust.min',
            'Fields': {
                'name': 'name_test_1',
                'value': 3
                }
            })
        self.send_json({
            'Timestamp': 14000000000,
            'Type': 'test.gust.min',
            'Fields': {
                'name': 'name_test_2',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 16010000000,
            'Type': 'test.gust.min',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        # name_test_1 gust min value is 2 because it is the first received
        # value and so there is no previous value to aggregate with
        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'min')
        self.assertEqual(data['Fields']['_tick'], 3)
        self.assertTrue('_gust' in data['Fields'])
        self.assertEqual(data['Fields']['_gust'], 2)

    def test_sandbox_gust_max(self):
        self.send_json({
            'Timestamp': 10000000000,
            'Type': 'test.gust.max',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 11500000000,
            'Type': 'test.gust.max',
            'Fields': {
                'name': 'name_test_1',
                'value': 6
                }
            })
        self.send_json({
            'Timestamp': 13000000000,
            'Type': 'test.gust.max',
            'Fields': {
                'name': 'name_test_1',
                'value': 3
                }
            })
        self.send_json({
            'Timestamp': 14000000000,
            'Type': 'test.gust.max',
            'Fields': {
                'name': 'name_test_2',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 16010000000,
            'Type': 'test.gust.max',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 4.5)
        self.assertEqual(data['Fields']['name_test_2'], 5)
        self.assertEqual(data['Fields']['_agg'], 'max')
        self.assertEqual(data['Fields']['_tick'], 3)
        self.assertTrue('_gust' in data['Fields'])
        self.assertEqual(data['Fields']['_gust'], 2)

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 5)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'max')
        self.assertEqual(data['Fields']['_tick'], 3)
        self.assertFalse('_gust' in data['Fields'])

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'min')
        self.assertEqual(data['Fields']['_tick'], 3)

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['name_test_2'], 1)
        self.assertEqual(data['Fields']['_agg'], 'count')
        self.assertEqual(data['Fields']['_tick'], 3)

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 5)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'last')
        self.assertEqual(data['Fields']['_tick'], 3)

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 7)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'sum')
        self.assertEqual(data['Fields']['_tick'], 3)

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
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name_test_1'], 3.5)
        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'avg')
        self.assertEqual(data['Fields']['_tick'], 3)

    def test_sandbox_direct(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test.no',
            'Fields': {
                'name': 'name_test_1',
                'value': 2
                }
            })
        self.send_json({
            'Timestamp': 11,
            'Type': 'test.no',
            'Fields': {
                'name': 'name_test_1',
                'value': 5
                }
            })
        self.send_json({
            'Timestamp': 12,
            'Type': 'test.no',
            'Fields': {
                'name': 'name_test_2',
                'value': 3
                }
            })

        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]

        self.assertEqual(data['Fields']['name_test_1'], 2)
        self.assertEqual(data['Fields']['_agg'], 'no')
        self.assertEqual(data['Timestamp'], 10)
        self.assertFalse('name_test_2' in data['Fields'])
        self.assertFalse('_tick' in data['Fields'])
        self.assertFalse('_gust' in data['Fields'])

        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]

        self.assertEqual(data['Fields']['name_test_1'], 5)
        self.assertEqual(data['Fields']['_agg'], 'no')
        self.assertEqual(data['Timestamp'], 11)
        self.assertFalse('name_test_2' in data['Fields'])
        self.assertFalse('_tick' in data['Fields'])
        self.assertFalse('_gust' in data['Fields'])

        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]

        self.assertEqual(data['Fields']['name_test_2'], 3)
        self.assertEqual(data['Fields']['_agg'], 'no')
        self.assertEqual(data['Timestamp'], 12)
        self.assertFalse('name_test_1' in data['Fields'])
        self.assertFalse('_tick' in data['Fields'])
        self.assertFalse('_gust' in data['Fields'])


class TestGatherLastMetric(HekaTestCase):

    sandboxes = {'TestGatherLastMetricFilter': {
        'file': '%s/gather_last_metrics.lua' % HEKA_OLD_FILTERS_DIR,
        'toml': """
[TestGatherLastMetricFilter]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
ticker_interval = 2
[TestGatherLastMetricFilter.config]
type_output = "output"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'name_test_1',
                'value': 10
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'name_test_2',
                'value': 12
                }
            })
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'name_test_3',
                'value': 7
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
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
        'TestFormatMetricName': {
            'file': '%s/format_metric_name.lua' % HEKA_OLD_FILTERS_DIR,
            'toml': """
[TestFormatMetricName]
type = "SandboxFilter"
message_matcher = "Type == 'heka.sandbox.encode.influxdb'"
[TestFormatMetricName.config]
fields = "uuid name value"
separator = "-"
type_output = "output"
"""}}

    def test_sandbox(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Fields': {
                'name': 'name_test',
                'value': 10
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'uuid_test-name_test-10', 'name field should be set to: uuid_test-name_test-10')


class TestTrserverData(HekaTestCase):

    sandboxes = {}

    def send_trserver(self, msg):
        print "=> %s" % json.dumps(msg)
        self.heka_output.sendto(
            msg, ('localhost', int(ENV['TRSERVER_OUTPUT_PORT'])))

    def test_sandbox(self):
        self.send_trserver('trserver_tracker01_accelerometer:300|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_accelerometer')
        self.assertEqual(data['Fields']['value'], 300)
        self.assertFalse('_mode' in data['Fields'])

        self.send_trserver('trserver_sun_roll:-51.842|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_sun_roll')
        self.assertEqual(data['Fields']['value'], -51.842)
        self.assertFalse('_mode' in data['Fields'])

        self.send_trserver('trserver_tracker01_mode:5|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_mode')
        self.assertEqual(data['Fields']['value'], 5)
        self.assertTrue('_mode' in data['Fields'])
        self.assertEqual(data['Fields']['_mode'], 5)

        self.send_trserver('trserver_tracker01_wind:11.4|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_wind')
        self.assertEqual(data['Fields']['value'], 11.4)
        self.assertTrue('_mode' in data['Fields'])
        self.assertEqual(data['Fields']['_mode'], 5)

        self.send_trserver('trserver_tracker01_accelerometer:300|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_tracker01_accelerometer')
        self.assertEqual(data['Fields']['value'], 300)
        self.assertTrue('_mode' in data['Fields'])
        self.assertEqual(data['Fields']['_mode'], 5)

        self.send_trserver('trserver_sun_roll:-51.842|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_sun_roll')
        self.assertEqual(data['Fields']['value'], -51.842)
        self.assertFalse('_mode' in data['Fields'])

        self.send_trserver('trserver_tracker02_accelerometer:300|p\n')
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['Fields']['name'], 'trserver_tracker02_accelerometer')
        self.assertEqual(data['Fields']['value'], 300)
        self.assertFalse('_mode' in data['Fields'])


class TestLogData(HekaTestCase):

    def setUp(self):
        self.heka_log_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_log_input.bind(('localhost', int(ENV['LOG_INPUT_PORT'])))

    def tearDown(self):
        self.heka_log_input.close()

    sandboxes = {
        'TestDecodeLogMetric': {
            'file': '%s/decode_metric.lua' % HEKA_OLD_FILTERS_DIR,
            'toml': """
[TestDecodeLogMetric]
type = "SandboxFilter"
message_matcher = "Type == 'log.input' && Fields[decoder_type] == 'metric'"
[TestDecodeLogMetric.config]
type_output = "encode.log.metric"
"""},
        'TestEncodeLogMetric': {
            'file': '%s/encode_metric.lua' % HEKA_OLD_FILTERS_DIR,
            'toml': """
[TestEncodeLogMetric]
type = "SandboxFilter"
message_matcher = "Type == 'heka.sandbox.encode.log.metric'"
    [TestEncodeLogMetric.config]
    type_output = "log.output"
"""},
        'TestDecodeLogEvent': {
            'file': '%s/decode_event.lua' % HEKA_OLD_FILTERS_DIR,
            'toml': """
[TestDecodeLogEvent]
type = "SandboxFilter"
message_matcher = "Type == 'log.input' && Fields[decoder_type] == 'event'"
[TestDecodeLogEvent.config]
type_output = "encode.log.event"
"""},
        'TestEncodeLogEvent': {
            'file': '%s/encode_event.lua' % HEKA_OLD_FILTERS_DIR,
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


class TestEncodeCarbon(HekaTestCase):

    def setUp(self):
        self.heka_log_input = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heka_log_input.bind(('localhost', int(ENV['CARBON_INPUT_PORT'])))

    def tearDown(self):
        self.heka_log_input.close()

    sandboxes = {}

    def receive_carbon(self):
        data, _ = self.heka_log_input.recvfrom(MAX_BYTES)
        return data

    def test_sandbox_metric(self):
        self.send_json({
            'Timestamp': 10000000000,
            'Type': 'carbon.output',
            'Severity': 7,
            'Fields': {
                'm_1': 1.2,
                'm_2': 0,
                '_agg': 'min',
                '_tick': 3,
                }
            })
        data = self.receive_carbon()
        self.assertEqual(
            data,
            'd539a1ab-1742-43c5-982e-02fab58283fa.hl-mc-1-dev.m_1 1.2 10\n'
            'd539a1ab-1742-43c5-982e-02fab58283fa.hl-mc-1-dev.m_2 0 10\n')


class TestEncodeInflux08(HekaTestCase):

    sandboxes = {'TestEncodeInflux08': {
        'file': '%s/encode_influxdb_0_8.lua' % HEKA_FILTERS_DIR,
        'toml': """
[TestEncodeInflux08]
type = "SandboxFilter"
message_matcher = "Type == 'test'"
ticker_interval = 2
[TestEncodeInflux08.config]
type_output = "output"
"""}}

    def test_sandbox_metric(self):
        self.send_json({
            'Timestamp': 10,
            'Type': 'test',
            'Severity': 7,
            'Fields': {
                'm_1': 1.2,
                'm_2': 0,
                '_agg': 'min',
                '_tick': 3,
                }
            })
        self.send_json({
            'Timestamp': 15,
            'Type': 'test',
            'Severity': 7,
            'Fields': {
                'm_1': 1,
                '_agg': 'max',
                '_tick': 3,
                }
            })
        data = self.receive_json()
        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertGreater(len(data['Payload']), 0)
        payload = json.loads(data['Payload'])
        self.assertDictEqual(payload[0],
            {
                u'points': [[0.01, 1.2]],
                u'name': u'm_1',
                u'columns': [u'time', u'value']
            })
        self.assertDictEqual(payload[1],
            {
                u'points': [[0.01, 0]],
                u'name': u'm_2',
                u'columns': [u'time', u'value']
            })
        self.assertDictEqual(payload[2],
            {
                u'points': [[0.015, 1]],
                u'name': u'm_1',
                u'columns': [u'time', u'value']
            })


if __name__ == '__main__':
    unittest.main()
