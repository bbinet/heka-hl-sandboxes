require "cjson"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local emit_timestamp_in_sec = read_config('emit_timestamp_in_sec') or false
local timestamp = 1
local metrics = {}

if emit_timestamp_in_sec ~= false and emit_timestamp_in_sec ~= true then
    error('you must initialize "emit_timestamp_in_sec" option: allowed value "true", default: "false"')
else
    timestamp = 1e9
end

function process_message()
    local metric = {
	name = read_message("Fields[name]"),
	columns = {'time', 'value'},
	points = {{read_message("Timestamp") / timestamp, read_message("Fields[value]")}}
    }
    metrics[#metrics+1] = metric

    return 0
end

function timer_event(ns)
    inject_message({
	Type = type_output,
	Payload = cjson.encode(metrics)
    })
    metrics = {}
end
