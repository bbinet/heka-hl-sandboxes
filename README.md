HEKA Data collection and processing
===================================

Install
------------

To install heka, do following step

    $ sudo apt-get install heka
    $ git clone git@bitbucket.org:helioslite/heka-hl-sandboxes.git
    $ cd heka-hl-sandboxes
    $ cp -r hekaconfig ~
    $ cp decoders/* /usr/share/heka/lua_decoders
    $ cp encoders/* /usr/share/heka/lua_encoders
    $ cp filters/* /user/share/heka/lua_filters
    $ cp modules/* /usr/share/heka/lua_modules

Run
---

To run heka, do the following step

    $ sudo hekad -config hekaconfig

Config
------

To set uuid prefixe, edit `heka.toml` file

    [TrserverParse.config]
    uuid = "uuid_name"

To change the default configuration, edit `config.toml` file

    $ vi ~/.hekaconfig/config.toml

Dispatch statmetrics depending on the regex expression

    [Dispatcher.config]
    list = "label1 label2"
    label1_regex = "regex_expression_1"
    label1_sandbox = "[ticker_interval]s-aggregation_1"
    label2_regex = "regex_expression_2"
    label2_sandbox = "[ticker_interval]s-aggregation_2"

    [Cbufs-[ticker_interval]s-aggregation_1]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.[ticker_interval]s-aggregation_1'"
    ticker_interval = ticker_interval
        [Cbufs-[ticker_interval]s-aggregation_1.config]
        aggregation = "aggregation"
        sec_per_row = integer
        nb_rows = integer
        next_sandbox = "[ticker_interval]s-aggregation_*"  #optional

    [Cbufs-[ticker_interval]s-aggregation_2]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.[ticker_interval]s-aggregation_2'"
    ticker_interval = ticker_interval
        [Cbufs-[ticker_interval]s-aggregation_2.config]
        aggregation = "aggregation"
        sec_per_row = integer
        nb_rows = integer
        next_sandbox = "[ticker_interval]s-aggregation_*"  #optional

* `ticker_interval` as integer (unit= second)
* `aggregation` as string (`"avg"`, `"sum"`, `"max"`, `"min"`)
* if `next_sandbox` is not configure metrics will be send to the output, else metrics will be send to sandbox indicated
* `"regex_expression_*"` receive a string corresponding to what you want to match, if you want to match everything write `"."`

Exemple for send the last metric every minute

    [Dispatcher.config]
    list = "label"
    label_regex = "roll_angle"
    label_sandbox = "60s-avg"

    [Cbufs-60s-avg]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.60s-avg'"
    ticker_interval = 60
        [Cbufs-60s-avg.config]
        aggregation = "avg"
        sec_per_row = 1
        nb_rows = 1

Debug
-----

To run debug mode, do the following command

    $ mv ~/hekaconfig/debug.toml.bak ~/hekaconfig/debug.toml

And run the next command

    socat udp-l:8126,fork STDOUT
