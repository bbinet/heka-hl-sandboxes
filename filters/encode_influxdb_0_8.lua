require "cjson"
require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local metrics = {}

function process_message()
    local timestamp = read_message('Timestamp')
    if timestamp == nil then
        return -1, "Timestamp can't be nil"
    end
    -- TODO: remove the division with the release from influxDB 0.9
    local ts = timestamp/1e3

    while true do
	typ, key, value = read_next_field()
	if not typ then break end
        -- exclude bytes and internal fields starting with '_' char
	if typ ~= 1 and key:match'^(.)' ~= '_' then
	    metrics[#metrics+1] = {
		name = key,
		columns = {'time', 'value'},
		points = {{ts, value}}
	    }
	end
    end

    return 0
end

function timer_event(ns)
    if next(metrics) ~= nil then
	inject_message({
	    Type = type_output,
	    Payload = cjson.encode(metrics)
	})
    end
    metrics = {}
end
