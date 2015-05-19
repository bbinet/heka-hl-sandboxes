## API

Here are the list of the old `heka-hl-sandboxes` sandboxes which are not used
in production anymore.

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

#### `decoders/decode_header.lua`

This sandbox parses messages from log files (generic header part only) and
forward them to a specific decoder filter (metric, event) for further decoding.

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

#### `filters/decode_event.lua`

This sandbox parses the event specific part of a log line.

#### `filters/decode_metric.lua`

This sandbox parses the metric specific part of a log line.

#### `filters/encode_event.lua`

This sandbox encodes events messages as a specific formatted string into the
payload for further processing of the `encode_header.lua` encoder.

#### `filters/encode_metric.lua`

This sandbox encodes metrics messages as a specific formatted string into the
payload for further processing of the `encode_header.lua` encoder.

#### `filters/format_metric_name.lua`

This sandbox sets the "name" field of the message by concatenating other
fields values.

* `fields(string "field1 field2")`: Space separated list of fields.
  Each field must refer to a field name which actually exists in the message.
  The concatenation of the fields values will keep the same order of the list.
* `separator(string)`: String separator to use concatenate all fields values.

#### `filters/gather_last_metrics.lua`

This sandbox gathers multiple metrics in the same message but keep only the
last value of every metric.

The `type_output_method` config option is not supported for this filter.

Custom configuration for this sandbox filter:

* `ticker_interval(int)`: Frequency (in seconds) at which a new message will be
  generated with last values for all gathered metrics.

