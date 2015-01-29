require "string"

local matcher = read_config('matchers') or error ('you must initialize "matchers" option')
local matchers = { }

for value in string.gmatch(matcher, "[%S]+") do
    matchers[#matchers + 1] = {
	type_output = read_config(value .. '_type_output') or error ('you must initialize "' .. value .. '_type_output" option'),
	regex = read_config(value .. '_regex') or error ('you must initialize "' .. value .. '_regex" option')
    }
end

function process_message()
    local fields = { }
    while true do
	typ, key, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[key] = value
	end
    end

    for index, item in ipairs(matchers) do
	if string.find(read_message('Fields[name]'), "^" .. item.regex .. "$") ~= nil then
	    inject_message({
		Type = item.type_output,
		Timestamp = read_message('Timestamp'),
		Payload = read_message('Payload'),
		Fields = fields
	    })
	    break
	end
    end

    return 0
end
