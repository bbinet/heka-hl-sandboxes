require "string"
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local trackers_mode = {}

function process_message()
    local name, value = string.match(read_message('Payload'), "^([%w_.]+):([%w_.+-]+)|p\n$")
    value = tonumber(value)
    if name == nil then
	return -1, "name can't be nil"
    end
    if value == nil then
	return -1, "value can't be nil"
    end

    local msg = {
        Type = type_output,
        Fields = {
            name = name,
            value = value
        }
    }

    local tracker = string.match(name, "^trserver_tracker(%d%d).*$")
    if tracker ~= nil then
	if string.find(name, "^trserver_tracker%d%d_mode$") then
	    trackers_mode[tracker] = tonumber(value)
	end
	msg['Fields']['_mode'] = trackers_mode[tracker]
    end

    inject_message(msg)

    return 0
end
