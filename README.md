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

    $ sudo hekad -config path/to/heka/toml

Config
------
To change the heka configuration, edit `path/to/heka-hl-sandboxes/toml/heka.toml` file

Edit the maximum number of times a message can be re-injected into the system. The default is 4.
[hekad]
max_message_loops = 5


To change the heka filter configuration, edit `path/to/heka-hl-sandboxes/toml/config.toml`
To add fields in message add this sandbox as following
    [SetNameFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/to_fields.lua"
    message_matcher = "Type == 'previous_sandbox'"
        [SetNameFilter.config]
        matchers = "uuid hostname"
        uuid = "d539a1ab-1742-43c5-982e-02fab58283fa"
        hostname = "hl-mc-1-dev"
        type_output = "next_sandbox"


To dispatch statmetrics depending on the regex expression
    [InfluxDispatcherFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/dispatcher.lua"
    message_matcher = "Type == 'heka.statmetric'"
        [InfluxDispatcherFilter.config]
        matchers = "windMetric allMetrics"
        allMetrics_regex = ".*"
        allMetrics_type_output = "5s.avg"
        windMetric_regex = "wind"
        windMetric_type_output = "3s.avg"

To do last aggregation (every minute)

    [TrwebclientFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/operation.lua"
    message_matcher = "Type == 'previous_sandbox'"
    ticker_interval = 60
        [TrwebclientFilter.config]
        aggregation = "last"
        type_output = "next_sandbox"

To do gust aggregation (max value of the 3s avg values in 1 minute)

    [Gust3sAvgFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.3s.avg'"
    ticker_interval = 3
        [Gust3sAvgFilter.config]
        aggregation = "avg"
        sec_per_row = 1
        nb_rows = 3
        type_output = "60s.max"

    [Gust60sMaxFilter]
    type = "SandboxFilter"
    filename = "/path/to/heka-hl-sandboxes/toml/filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.60s.max'"
    ticker_interval = 60
        [Gust60sMaxFilter.config]
        aggregation = "max"
        sec_per_row = 1
        nb_rows = 60
        type_output = "addFields"

* `ticker_interval` as integer (unit= second)
* `aggregation` as string (`"avg"`, `"sum"`, `"max"`, `"min"`, `"last"`)
* if `type_output` is mandatory
* `"regex_expression_*"` receive a string corresponding to what you want to match: (http://lua-users.org/wiki/PatternsTutorial)

Load Filter
-----------

To load a filter, run the following command

    heka-sbmgr -action=load -config=PlatformDevs.toml -script=sandbox_file.lua -scriptconfig=configDev.toml

Unload Filter
-------------

To unload a filter, run the next command

    heka-sbmgr -action=unload -config=PlatformDevs.toml -filtername=[FilterName]

Debug
-----

To run debug mode, do the following command

    $ mv path/to/heka-hl-sandboxes/toml/debug.toml.bak path/to/heka-hl-sandbowes/toml/debug.toml
