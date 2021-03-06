# HeliosLite Heka lua sandboxes

![Data flow visualization](https://bitbucket.org/helioslite/heka-hl-sandboxes/raw/master/heka_detailed.png)

## Install Heka

You can download the latest Heka release from:

* https://github.com/mozilla-services/heka/releases [amd64, i386]
* https://github.com/bbinet/heka/releases [armhf]

Then install it with:

    $ sudo dpkg -i path/to/heka.deb

## Test HL sandboxes

To test Heka HL sandboxes, run the following commands:

    $ export HEKA_HL_DIR=path/to/heka-hl-sandboxes/
    $ cd $HEKA_HL_DIR
    $ python -m unittest -b tests

Or to run a single test:

    $ python -m unittest -b tests.TestLogData

## Configure

Increase `max_message_loops` and `max_timer_inject` global config values in the
`[hekad]` configuration so that the same message can be processed in many
sandboxes, and a single sandbox can generate many messages (e.g.
`aggregate_metric.lua` sandbox filter needs this):

    [hekad]
    max_message_loops = 10
    max_timer_inject = 200

For better understanding of Heka global configuration option, see:
https://hekad.readthedocs.org/en/latest/config/index.html#global-configuration-options

Sample configuration files and more configuration documentation are
available in the `toml` directory.

## Run

To run Heka with the sample configuration, you can do:

    $ export CARBON_OUT_DIR=/tmp
    $ export HEKA_HL_DIR=path/to/heka-hl-sandboxes/
    $ hekad -config $HEKA_HL_DIR/toml

### Debug

To see all messages flowing through Heka, you can add the following config:

    [RstEncoder]
    [LogOutput]
    message_matcher = "TRUE"
    encoder = "RstEncoder"

Or you can output only some messages by specifying a custom value for
`message_matcher`.

### Manage sandboxes dynamically

To load dynamically a new filter, run the following command:

    heka-sbmgr -config=$HEKA_HL_DIR/PlatformDevs.toml \
        -action=load -script=sandbox_file.lua -scriptconfig=configDev.toml

To unload the previous dynamic filter, run:

    heka-sbmgr -config=$HEKA_HL_DIR/PlatformDevs.toml \
        -action=unload -filtername=[FilterName]

## API

Here are the list of all sandboxes available in `heka-hl-sandboxes` repository.

### Sandbox decoders

Common configuration:

* `type(string)`: Sandbox type (should be: `SandboxDecoder`).
* `filename(string)`: Path to the lua sandbox filter.
* `message_matcher(string)`: Message matcher which determines wether or not
  the sandbox filter should be run.
* `type_output(string)`: Sets the message `Type` header to the specified
  value.

Here is the list of common Heka sandbox parameters:
https://hekad.readthedocs.org/en/latest/config/common_sandbox_parameter.html

#### `decoders/decode_json.lua`

This sandbox parses messages from json.

* `allowed_headers(string)`: Single or multiple (space separated list) headers
  to include in the new message. If `nil`, all standard headers will be set.

#### `decoders/decode_statsdp.lua`

This sandbox parses metrics in the statsdp format (statsd proxy mode):
`name:value|p\n`

It also adds a `_mode` field to all tracker messages which value is set to
the last mode metric value that have been received for the same tracker.

### Sandbox encoders

Common configuration:

* `type(string)`: Sandbox type (should be: `SandboxEncoder`).
* `filename(string)`: Path to the lua sandbox filter.
* `message_matcher(string)`: Message matcher which determines wether or not
  the sandbox filter should be run.

#### `encoders/encode_carbon.lua`

This sandbox encodes metrics to the plaintext carbon format so that it can be
ingested by a carbon (graphite) server.

See: http://graphite.readthedocs.org/en/latest/feeding-carbon.html#the-plaintext-protocol

#### `encoders/encode_json.lua`

This sandbox encodes a message to JSON.

* `allowed_headers(string)`: Single or multiple (space separated list) headers
  to include in the json. If `nil`, all standard headers will be included.

### Sandbox filters

Common configuration:

* `type(string)`: Sandbox type (should be: `SandboxFilter`).
* `filename(string)`: Path to the lua sandbox filter.
* `message_matcher(string)`: Message matcher which determines wether or not
  the sandbox filter should be run.
* `type_output(string)`: Sets the message `Type` header to the specified
  value (will be prefixed with `heka.sandbox.`).
* `type_output_method([prefix|suffix|overwrite])`: Determines how the
  `type_output` string should be set on the `Type` header (default is
  "overwrite").

#### `filters/add_static_fields.lua`

This sandbox sets hardcoded values for given fields.

* `fields(string "field1 field2")`: Space separated list of fields.
  Each field refers to another configuration option that specify the value of
  the field to hardcode.
* `<fieldname>(string)`: Value of the static field "fieldname" to set.

#### `filters/aggregate_metric.lua`

This sandbox aggregates metric values according to an aggregate method
(average, minimum, maximum, sum, last).

The `type_output_method` config option is not supported for this filter.

Custom configuration for this sandbox filter:

* `ticker_interval(int)`: Frequency (in seconds) at which a new aggregated
  metric will be generated. *This should be set both in the common and custom
  config sections.*
* `gust(int|nil)`: Wether or not to apply a "gust" average pretreatment. If
  gust is not nil, it must be the number of seconds (integer) from which an
  average of previous values will be computed and used instead of the raw value
  received.
* `aggregation(string)`: Aggregation method. Allowed aggregation methods are:
    * `avg`: Average calulation.
    * `min`: Mimimum value received.
    * `max`: Maximum value received.
    * `sum`: Sum calculation.
    * `last`: Last value received.
    * `count`: Number of metric values received.
    * `no`: Don't do any aggregation, but forward metrics as soon as they
                arrive in the aggregated format.

#### `filters/encode_influxdb_0_8.lua`

This sandbox gathers multiple metrics, groups and encodes them by batch as json
before sending to InfluxDB.
The sandbox will store the encoded json string in the payload, so this can then
be sent to a HttpOutput configured with a PayloadEncoder.

The `type_output_method` config option is not supported for this filter.

Custom configuration for this sandbox filter:

* `ticker_interval(int)`: Frequency (in seconds) at which a new batch metric
  will be generated.

#### `filters/regex_dispatch_metric.lua`

This sandbox acts as a router: it dynamically sets the `type_output` header
value of a message depending on the metric name (regex matching).

Custom configuration for this sandbox filter:

* `matchers(string "item1 item2")`: Space separated list of matchers items.
  Each item refers to two other dedicated configuration options: `<item>_regex`
  and `<item>_type_output` (see below).
  The order is important, since every item will be tested sequentially: the
  first item that matches wins.
* `<item>_regex(string)`: Regular expression to match for metric names.
  (http://lua-users.org/wiki/PatternsTutorial)
* `<item>_type_output(string)`: Sets the message `Type` header to the specified
  value (will be prefixed with `heka.sandbox.`).

## Graphviz schema

You can update the heka-hl-sandboxes schema image with the following Graphviz command:

    $ dot -Tpng heka_detailed.dot -o heka_detailed.png

