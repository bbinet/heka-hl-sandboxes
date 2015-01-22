require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local park_type_output = read_config('park_type_output') or error('you must initialize "park_type_output" option')
local to_discard = { }

function process_message()
    local typ = type_output
    local name = read_message('Fields[name]')
    local value = read_message('Fields[value]')
    local tracker = string.match(name, "^.*tracker(..).*$")

    if tracker ~= nil then
	if string.find(name, "^.*mode$") then
	    if tonumber(value) == 2 then
		if to_discard[tracker] then
		    typ = park_type_output
		end
		to_discard[tracker] = true
	    elseif to_discard[tracker] then
		to_discard[tracker] = false
	    end
	elseif to_discard[tracker] then
	    typ = park_type_output
	end
    end

    inject_message({
	Type = typ,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Fields = {
	    name = name,
	    value = value
	}
    })

    return 0
end
