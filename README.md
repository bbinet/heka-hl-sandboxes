HEKA Data collection and processing
===================================

Install
------------

Get and and install heka with this following link https://github.com/mozilla-services/heka/releases

To get heka configuration do following step

    $ git clone git@bitbucket.org:helioslite/heka-hl-sandboxes.git

Actual configuration from heka-hl-sandboxes
![alt text](https://bitbucket.org/helioslite/heka-hl-sandboxes/raw/master/heka_detailed.png)

Run
---

To run heka, do the following step

    $ export HEKA_PLUGINS_BASE_DIR=path/to/heka-hl-sandboxes
    $ sudo hekad -config $HEKA_PLUGINS_BASE_DIR/heka-hl-sandboxes/toml

API
---
All the sandboxes filters describe below are these main common parameters

* type(string): sandbox type
* filename(string): path to the sandbox from the racine
* message_matcher(string): message matching by the sandbox (https://hekad.readthedocs.org/en/v0.8.2/message_matcher.html)

Configuration for each sandbox

__decoder/trserver_decode_metrics.lua:__ This sandbox catch metrics from trserver and parse it into the fields

* type_output(string): __name__ for the next sandbox.

__decoder/decode_header.lua:__ This sandbox will parse message from log file and send to the right decoder filter (metric, event, alert)

* type_output(string): __name__ for the next sandbox.

__filters/decode_alert.lua:__ This sandbox will parse alert log into the right field

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/decode_event.lua:__ This sandbox will parse event log into the right field

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/decode_metric.lua:__ This sandbox will parse metric log into the right field

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/regex_metric_dispatch.lua:__ This sandbox will send dispatch each metric in function of this metric name to the sandbox corresponding

* matchers(string "arg1 arg2"): take arguments with as separator a whitespace. Each arguments will prefix the following parameters. The order of these arguments is important!
* arg1_regex(string): regular expression to catch metric (http://lua-users.org/wiki/PatternsTutorial)
* arg1_type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.
* arg2_regex(string): regular expression to catch metric (http://lua-users.org/wiki/PatternsTutorial)
* arg2_type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/aggregate_metric.lua:__ This sandbox will aggregate the value in function of the aggregation type

* ticker_interval(int): Frequency (in seconds) that a timer event will be sent to the filter.
* aggregation(string): value allow are: "avg", "last", "min", "max", "sum". This value can be multiple with a whitespace as delimiter.
* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/add_static_fields.lua:__ This sandbox will be add new Fields to the message

* fields(string "arg1 arg2"): take arguments with as separator a whitespace. Each arguments will be the name of the field added.
* arg1(string): value of the field arg1
* arg2(string): value of the field arg2
* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/format_metric_name.lua:__ This sandbox will be concatenate field with the separator defined

* fields(string "arg1 arg2"): take arguments with as separator a whitespace. Each arguments must correspond to a field name. The order of these arguments is important!
* separator(string): the string which will separate fields value
* emit_timestamp_in_sec(boolean): convert timestamp in second instead of nanosecond
* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/gather_last_metrics.lua:__ This sandbox will be group different metric in the same message

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/add_mode_field.lua:__ This sandbox will add a field with the mode of the tracker

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/encode_alert.lua:__ This sandbox will dump alert message into the payload

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/encode_event.lua:__ This sandbox will dump event message into the payload

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__filters/encode_metric.lua:__ This sandbox will dump metric message into the payload

* type_output(string): __suffix__ name for the next sandbox. The base name is heka.sandbox.

__encoders/encode_header.lua:__ This sandbox will dump metric, alert or event data into the payload

__encoders/metrics_encode_json.lua:__ This sandbox dump data from fields to a JSON object

Config
------
To change the heka configuration, edit `path/to/heka-hl-sandboxes/toml/heka.toml` file

Edit the maximum number of times a message can be re-injected into the system. The default is 4.

    [hekad]
    max_message_loops = 5

Edit the maximum number of messages that a sandbox filter’s TimerEvent function can inject in a single call; the default is 10.

    [hekad]
    max_timer_inject = 100

Decoder which recept metrics from trserver and parse it

    [TrServerDecoder]
    type = "SandboxDecoder"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/decoders/trserver_decode_metrics.lua"
        [TrServerDecoder.config]
        type_output = "heka.statmetric"

To change the trwebclient configuration, edit `path/to/heka-hl-sandboxes/toml/trwebclient-stream.toml` file

Encoder which encode data in json format

    [ServerEncoder]
    type = "SandboxEncoder"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/encoders/metrics_encode_json.lua"


To change the heka filter configuration in order to send data to influxDB, edit `path/to/heka-hl-sandboxes/toml/influx.toml`

To group metrics in a same message add this sandbox as following

    [GroupMetricsFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/gather_last_metrics.lua"
    message_matcher = "Type == 'heka.sandbox.group'"
    ticker_interval = 1
        [GroupMetricsFilter.config]
        type_output = "trwebclient"

To add fields in message add this sandbox as following

    [SetUuidHostnameFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/add_static_fields.lua"
    message_matcher = "Type == 'previous_sandbox'"
        [SetUuidHostnameFilter.config]
        fields = "uuid hostname"
        uuid = "d539a1ab-1742-43c5-982e-02fab58283fa"
        hostname = "hl-mc-1-dev"
        type_output = "next_sandbox"

To dispatch statmetrics depending on the regex expression

    [MainDispatchFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/regex_dispatch_metric.lua"
    message_matcher = "Type == 'heka.statmetric'"
        [MainDispatchFilter.config]
        matchers = "windMetric allMetrics"
        allMetrics_regex = ".*"
        allMetrics_type_output = "5s.avg"
        windMetric_regex = ".*wind"
        windMetric_type_output = "3s.avg"

To do last aggregation (every minute)

    [60sLastFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/aggregate_metric.lua"
    message_matcher = "Type == 'previous_sandbox'"
    ticker_interval = 60
        [60sLastFilter.config]
        aggregation = "last"
        type_output = "next_sandbox"

To do gust aggregation (max value of the 3s avg values in 1 minute)

    [Gust3sAvgFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.3s.avg'"
    ticker_interval = 3
        [Gust3sAvgFilter.config]
        aggregation = "avg"
        type_output = "60s.max"

    [Gust60sMaxFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.60s.max'"
    ticker_interval = 60
        [Gust60sMaxFilter.config]
        aggregation = "max"
        type_output = "next_sandbox"

Filter which prepare metrics to be send to influxdb with influx encoder

    [Statmetric-influx-preEncoder]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_PLUGINS_BASE_DIR]/heka-hl-sandboxes/toml/filters/format_metric_name.lua"
    message_matcher = "Type == 'heka.sandbox.encode.influx'"
        [Statmetric-influx-preEncoder.config]
        fields = "uuid hostname name"
        separator = "."
        type_output = "influx"

* `ticker_interval` as integer (unit= second)
* `aggregation` as string (`"avg"`, `"sum"`, `"max"`, `"min"`, `"last"`)
* all the options are mention and are mandatory execpt `sec_per_row` and `nb_rows` when `aggregation` is `last`
* `"regex_expression_*"` receive a string corresponding to what you want to match: (http://lua-users.org/wiki/PatternsTutorial)

Load Filter
-----------

To load a filter, run the following command

    heka-sbmgr -action=load -config=$HEKA_PLUGINS_BASE_DIR/heka-hl-sandboxes/PlatformDevs.toml -script=sandbox_file.lua -scriptconfig=configDev.toml

Unload Filter
-------------

To unload a filter, run the next command

    heka-sbmgr -action=unload -config=$HEKA_PLUGINS_BASE_DIR/heka-sandboxes/PlatformDevs.toml -filtername=[FilterName]

Debug
-----
Debug mode provide us to see data from payload on the standard output
To run debug mode, do the following command

    $ mv $HEKA_PLUGINS_BASE_DIR/heka-hl-sandboxes/toml/debug.toml.bak $HEKA_PLUGINS_BASE_DIR/heka-hl-sandbowes/toml/debug.toml

And edit debug.toml as following
    [RstEncoder]
    [LogOutput]
    message_matcher = "Type == 'next_sandbox'"
    encoder = "RstEncoder"
