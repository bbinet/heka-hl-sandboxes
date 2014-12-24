HEKA Data collection and processing
===================================

Install
------------

To install heka, do following step

    $ docker pull bbinet/heka
    $ git clone git@bitbucket.org:helioslite/heka-hl-sandboxes.git

Run
---

To run heka, do the following step

    $ sudo docker run --rm --name heka --link influxdb:influxdb \
    $ -v path/to/heka-hl-sandboxes:/config \
    $ -p 4354:4354 -p 8125:8125/udp \
    $ bbinet/heka

Config
------

To set uuid prefix, edit `path/to/heka-hl-sandboxes/toml/heka.toml` file

    [TrserverParse.config]
    uuid = "d539a1ab-1742-43c5-982e-02fab58283fa"

To change the default configuration, edit `path/to/heka-hl-sandboxes/toml/config.toml` file

    $ vi path/to/heka-hl-sandboxes/toml/config.toml

Dispatch statmetrics depending on the regex expression
Exemple for send the last metric every minute

    [Dispatcher.config]
    list = "label1 label2"
    label1_regex = "roll_angle"
    label1_sandbox = "60s-avg"
    label2_regex = "sun_tilt"
    label2_sandbox = "60s-aggregation_2"

    [Filter-aggregation_1]
    type = "SandboxFilter"
    filename = "filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.60s-avg'"
    ticker_interval = 60
        [Filter-aggregation_1.config]
        aggregation = "avg"
        sec_per_row = 1
        nb_rows = 1

    [Filter-aggregation_2]
    type = "SandboxFilter"
    filename = "filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.60s-aggregation_2'"
    ticker_interval = 240
        [Filter-aggregation_2.config]
        aggregation = "sum"
        sec_per_row = 60
        nb_rows = 1
        type_output = "60s-avg"

* `ticker_interval` as integer (unit= second)
* `aggregation` as string (`"avg"`, `"sum"`, `"max"`, `"min"`)
* if `next_sandbox` is not configure metrics will be send to the output, else metrics will be send to sandbox indicated
* `"regex_expression_*"` receive a string corresponding to what you want to match, if you want to match everything write `"."`

Debug
-----

To run debug mode, do the following command

    $ mv path/to/heka-hl-sandboxes/toml/debug.toml.bak path/to/heka-hl-sandbowes/toml/debug.toml
