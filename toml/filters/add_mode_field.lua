require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local trackers_mode = { }

function process_message()
    local fields = { }
    while true do
	typ, key, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[key] = value
	end
    end

    local tracker = string.match(fields.name, "^trserver_tracker(%d%d).*$")
    if tracker ~= nil then
	if string.find(fields.name, "^trserver_tracker%d%d_mode$") then
	    trackers_mode[tracker] = tonumber(fields.value)
	end
	fields['mode'] = trackers_mode[tracker]
    end

    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Fields = fields
    })
    return 0
end
