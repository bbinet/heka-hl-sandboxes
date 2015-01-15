HEKA Data collection and processing
===================================

Install
------------

Get and and install heka with this following link https://github.com/mozilla-services/heka/releases

To get heka configuration do following step

    $ git clone git@bitbucket.org:helioslite/heka-hl-sandboxes.git

Run
---

To run heka, do the following step

    $ sudo hekad -config path/to/heka-hl-sandboxes/toml

Config
------
To change the heka configuration, edit `path/to/heka-hl-sandboxes/toml/heka.toml` file

Edit the maximum number of times a message can be re-injected into the system. The default is 4.
    [hekad]
    max_message_loops = 5

Decoder which recept metrics from trserver and parse it
    [TrServerDecoder]
    type = "SandboxDecoder"
    filename = "/home/helioslite/heka-hl-sandboxes/toml/decoders/trserver_decode_metrics.lua"
        [TrServerDecoder.config]
        type_output = "heka.statmetric"

Filter which prepare metrics to be send to influxdb with influx encoder
    [Statmetric-influx-preEncoder]
    type = "SandboxFilter"
    filename = "/home/helioslite/heka-hl-sandboxes/toml/filters/format_metric_name.lua"
    message_matcher = "Type == 'heka.sandbox.output'"
        [Statmetric-influx-preEncoder.config]
        fields = "uuid hostname name"
        splitter = "."
        type_output = "influx"

Encoder which encode data in json format
    [ServerEncoder]
    type = "SandboxEncoder"
    filename = "/home/helioslite/heka-hl-sandboxes/toml/encoders/metrics_encode_json.lua"


To change the heka filter configuration, edit `path/to/heka-hl-sandboxes/toml/config.toml`

To group metrics in a same message add this sandbox as following
    [GroupMetricsFilter]
    type = "SandboxFilter"
    filename = "/home/helioslite/heka-hl-sandboxes/toml/filters/gather_last_metrics.lua"
    message_matcher = "Type == 'heka.sandbox.group'"
    ticker_interval = 1
        [GroupMetricsFilter.config]
        type_output = "trwebclient"

To add fields in message add this sandbox as following
    [SetUuidHostnameFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/add_static_fields.lua"
    message_matcher = "Type == 'previous_sandbox'"
        [SetUuidHostnameFilter.config]
        fields = "uuid hostname"
        uuid = "d539a1ab-1742-43c5-982e-02fab58283fa"
        hostname = "hl-mc-1-dev"
        type_output = "next_sandbox"


To dispatch statmetrics depending on the regex expression
    [MainDispatchFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/regex_dispatch_metric.lua"
    message_matcher = "Type == 'heka.statmetric'"
        [MainDispatchFilter.config]
        matchers = "windMetric allMetrics"
        allMetrics_regex = ".*"
        allMetrics_type_output = "5s.avg"
        windMetric_regex = "wind"
        windMetric_type_output = "3s.avg"

To do last aggregation (every minute)

    [60sLastFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/cbuf_aggregate_metric.lua"
    message_matcher = "Type == 'previous_sandbox'"
    ticker_interval = 60
        [60sLastFilter.config]
        aggregation = "last"
        type_output = "next_sandbox"

To do gust aggregation (max value of the 3s avg values in 1 minute)

    [Gust3sAvgFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/cbuf_aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.3s.avg'"
    ticker_interval = 3
        [Gust3sAvgFilter.config]
        aggregation = "avg"
        sec_per_row = 1
        nb_rows = 3
        type_output = "60s.max"

    [Gust60sMaxFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/cbuf_aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.60s.max'"
    ticker_interval = 60
        [Gust60sMaxFilter.config]
        aggregation = "max"
        sec_per_row = 1
        nb_rows = 60
        type_output = "next_sandbox"

* `ticker_interval` as integer (unit= second)
* `aggregation` as string (`"avg"`, `"sum"`, `"max"`, `"min"`, `"last"`)
* all the options are mention and are mandatory execpt `sec_per_row` and `nb_rows` when `aggregation` is `last`
* `"regex_expression_*"` receive a string corresponding to what you want to match: (http://lua-users.org/wiki/PatternsTutorial)

Load Filter
-----------

To load a filter, run the following command

    heka-sbmgr -action=load -config=/path/to/heka-hl-sandboxes/PlatformDevs.toml -script=sandbox_file.lua -scriptconfig=configDev.toml

Unload Filter
-------------

To unload a filter, run the next command

    heka-sbmgr -action=unload -config=/path/to/heka-sandboxes/PlatformDevs.toml -filtername=[FilterName]

Debug
-----
Debug mode provide us to see data from payload on the standard output
To run debug mode, do the following command

    $ mv path/to/heka-hl-sandboxes/toml/debug.toml.bak path/to/heka-hl-sandbowes/toml/debug.toml

And edit debug.toml as following

    [RstEncoder]
    [LogOutput]
    message_matcher = "Type == 'next_sandbox'"
    encoder = "RstEncoder"
