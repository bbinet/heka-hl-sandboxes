require "string"

local matchers = read_config('fields') or error('you must initialize "fields" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = { }

for item in string.gmatch(matchers, "[%S]+") do
    fields[item] = read_config(item) or ('you must initialize "' .. item .. '" option')
end

function process_message()
    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then -- exclude bytes
	    fields[name] = value
	end
    end

    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })

    return 0
end
