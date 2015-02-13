require "cjson"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local metrics = {}

function process_message()
    local metric = {
	name = read_message("Fields[name]"),
	columns = {'time', 'value'},
	--TODO: remove the division with the release from influxDB 0.9
	points = {{read_message("Timestamp")/1e3, read_message("Fields[value]")}}
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
