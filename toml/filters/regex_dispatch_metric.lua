require "string"

local matcher = read_config('matchers') or error ('you must initialize "matchers" option')
local matchers = { }

for value in string.gmatch(matcher, "[%S]+") do
    local regex = read_config(value .. '_regex') or error ('you must initialize "' .. value .. '_regex" option')
    local type_output = read_config(value .. '_type_output') or error ('you must initialize "' .. value .. '_type_output" option')

    matchers[#matchers + 1] = {
	type_output = type_output,
	regex = regex
    }
end

function process_message()
    local name = read_message('Fields[name]')
    local type_output = nil

    for index, item in ipairs(matchers) do
	if string.find(name, "^" .. item.regex .. "$") ~= nil then
	    type_output = item.type_output
	    break
	end
    end

    if type_output ~= nil then
	inject_message({
	    Type = type_output,
	    Timestamp = read_message('Timestamp'),
	    Payload = read_message('Payload'),
	    Fields = {
		name = name,
		value = read_message('Fields[value]')
	    }
	})
    end
    return 0
end
