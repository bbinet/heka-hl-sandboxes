HEKA Data collection and processing
===================================

Install Heka:
-------------
    $ sudo apt-get install heka
    $ git clone git@bitbucket.org:helioslite/heka-hl-sandboxes.git
    $ cd heka-hl-sandboxes
    $ cp hekad.toml ~/.hekad.toml
    $ cp decoders/* /usr/share/heka/lua_decoders
    $ cp encoders/* /usr/share/heka/lua_encoders
    $ cp filters/* /user/share/heka/lua_filters
    $ cp modules/* /usr/share/heka/lua_modules

Run:
----
    $ sudo hekad -config .hekad.toml

Config:
-------

To change the default configuration::
    $ vi ~/.heka.toml

To set uuid prefixe, change the string value as following::
    [TrserverParse.config]
    uuid = "uuid_name"

To::
    [Dispatcher.config]
    list = "label1 label2 label3"
    label1_regex = "trserver_sun_roll"
    label1_sandbox = "5s-avg"
    label2_regex = "sun"
    label2_sandbox = "2s-min"
    label3_regex = "."
    label3_sandbox = "1s-max"

    [Cbufs-1s-max]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.1s-max'"
    ticker_interval = 1
        [Cbufs-5s-avg.config]
        aggregation = "max"
        sec_per_row = integer
        nb_rows = integer
        next_sandbox = "2s-min"  #optional

    [Cbufs-2s-min]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.2s-min'"
    ticker_interval = 2
        [Cbufs-5s-avg.config]
        aggregation = "min"
        sec_per_row = integer
        nb_rows = integer
        next_sandbox = "2s-min"  #optional

    [Cbufs-5s-avg]
    type = "SandboxFilter"
    filename = "lua_filters/operation.lua"
    message_matcher = "Type == 'heka.sandbox.5s-avg'"
    ticker_interval = 5
        [Cbufs-5s-avg.config]
        aggregation = "avg"
        sec_per_row = integer
        nb_rows = integer
        next_sandbox = "2s-min"  #optional
