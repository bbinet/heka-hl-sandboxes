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

#### `decoders/trserver_decode_metrics.lua`

This sandbox receives and parses metrics from trserver.

#### `decoders/decode_header.lua`

This sandbox parses messages from log files (generic header part only) and
forward them to a specific decoder filter (metric, event) for further decoding.

### Sandbox filters

Common configuration:

* `type(string)`: Sandbox type (should be: `SandboxFilter`).
* `filename(string)`: Path to the lua sandbox filter.
* `message_matcher(string)`: Message matcher which determines wether or not
  the sandbox filter should be run.
* `type_output(string)`: Sets the message `Type` header to the specified
  value (will be prefixed with `heka.sandbox.`).

#### `filters/decode_event.lua`

This sandbox parses the event specific part of a log line.

#### `filters/decode_metric.lua`

This sandbox parses the metric specific part of a log line.

#### `filters/regex_metric_dispatch.lua`

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

#### `filters/aggregate_metric.lua`

This sandbox aggregates metric values according to an aggregate method
(average, minimum, maximum, sum, last).

Custom configuration for this sandbox filter:

* `ticker_interval(int)`: Frequency (in seconds) at which a new aggregated
  metric will be generated.
* `aggregation(string)`: Single or multiple (space separated list) aggregation
  methods. Allowed aggregation methods are:
    * `avg`: Average calulation.
    * `min`: Mimimum value received.
    * `max`: Maximum value received.
    * `sum`: Sum calculation.
    * `last`: Last value received.
    * `count`: Number of metric values received.

#### `filters/add_static_fields.lua`

This sandbox sets hardcoded values for given fields.

* `fields(string "field1 field2")`: Space separated list of fields.
  Each field refers to another configuration option that specify the value of
  the field to hardcode.
* `<fieldname>(string)`: Value of the static field "fieldname" to set.

#### `filters/format_metric_name.lua`

This sandbox sets the "name" field of the message by concatenating other
fields values.

* `fields(string "field1 field2")`: Space separated list of fields.
  Each field must refer to a field name which actually exists in the message.
  The concatenation of the fields values will keep the same order of the list.
* `separator(string)`: String separator to use concatenate all fields values.

#### `filters/gather_metrics.lua`

This sandbox gathers multiple metrics, groups and encodes them by batch as json
before sending to InfluxDB.

* `ticker_interval(int)`: Frequency (in seconds) at which a new batch metric
  will be generated.

#### `filters/gather_last_metrics.lua`

This sandbox gathers multiple metrics in the same message but keep only the
last value of every metric.

* `ticker_interval(int)`: Frequency (in seconds) at which a new message will be
  generated with last values for all gathered metrics.

#### `filters/add_mode_field.lua`

This sandbox adds a "mode" field to all tracker messages which value is set to
the last mode metric value that have been received for the same tracker.

#### `filters/encode_event.lua`

This sandbox encodes events messages as a specific formatted string into the
payload for further processing of the `encode_header.lua` encoder.

#### `filters/encode_metric.lua`

This sandbox encodes metrics messages as a specific formatted string into the
payload for further processing of the `encode_header.lua` encoder.

### Sandbox encoders

Common configuration:

* `type(string)`: Sandbox type (should be: `SandboxEncoder`).
* `filename(string)`: Path to the lua sandbox filter.
* `message_matcher(string)`: Message matcher which determines wether or not
  the sandbox filter should be run.

#### `encoders/encode_header.lua`

This sandbox encodes the generic part of a message as a formatted string into
the payload (the metric or event specific part that has already been serialized
in above dedicated filters is copyed as is).

#### `encoders/metrics_encode_json.lua`

This sandbox encodes the timestamp and all message fields to JSON.

## Todo

* Issue #3 - test that sandboxes won't crash (but generate error messages) when
  receiving wrong inputs.
