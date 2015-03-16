# HL sandboxes configuration

This explains how to configure the HL sandboxes. An full working
example is also available in the `toml` directory.

Decoder which recept metrics from trserver and parse it

    [TrServerDecoder]
    type = "SandboxDecoder"
    filename = "%ENV[HEKA_HL_DIR]/decoders/trserver_decode_metrics.lua"
        [TrServerDecoder.config]
        type_output = "heka.statmetric"

To change the trwebclient configuration, edit `$HEKA_HL_DIR/toml/trwebclient-stream.toml` file

Encoder which encode data in json format

    [ServerEncoder]
    type = "SandboxEncoder"
    filename = "%ENV[HEKA_HL_DIR]/encoders/metrics_encode_json.lua"


To change the heka filter configuration in order to send data to influxDB, edit `$HEKA_HL_DIR/toml/influx.toml`

To group metrics in a same message add this sandbox as following

    [GroupMetricsFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/gather_last_metrics.lua"
    message_matcher = "Type == 'heka.sandbox.group'"
    ticker_interval = 1
        [GroupMetricsFilter.config]
        type_output = "trwebclient"

To add fields in message add this sandbox as following

    [SetUuidHostnameFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/add_static_fields.lua"
    message_matcher = "Type == 'previous_sandbox'"
        [SetUuidHostnameFilter.config]
        fields = "uuid hostname"
        uuid = "d539a1ab-1742-43c5-982e-02fab58283fa"
        hostname = "hl-mc-1-dev"
        type_output = "next_sandbox"

To dispatch statmetrics depending on the regex expression

    [MainDispatchFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/regex_dispatch_metric.lua"
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
    filename = "%ENV[HEKA_HL_DIR]/filters/aggregate_metric.lua"
    message_matcher = "Type == 'previous_sandbox'"
    ticker_interval = 60
        [60sLastFilter.config]
        aggregation = "last"
        type_output = "next_sandbox"

To do gust aggregation (max value of the 3s avg values in 1 minute)

    [Gust3sAvgFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.3s.avg'"
    ticker_interval = 3
        [Gust3sAvgFilter.config]
        aggregation = "avg"
        type_output = "60s.max"

    [Gust60sMaxFilter]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/aggregate_metric.lua"
    message_matcher = "Type == 'heka.sandbox.60s.max'"
    ticker_interval = 60
        [Gust60sMaxFilter.config]
        aggregation = "max"
        type_output = "next_sandbox"

Filter which prepare metrics to be send to influxdb with influx encoder

    [Statmetric-influx-preEncoder]
    type = "SandboxFilter"
    filename = "%ENV[HEKA_HL_DIR]/filters/format_metric_name.lua"
    message_matcher = "Type == 'heka.sandbox.encode.influx'"
        [Statmetric-influx-preEncoder.config]
        fields = "uuid hostname name"
        separator = "."
        type_output = "influx"
