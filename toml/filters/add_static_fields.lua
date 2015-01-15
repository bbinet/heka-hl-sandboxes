require "string"

local fields_cfg = read_config('fields') or error('you must initialize "fields" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = { }

for item in string.gmatch(fields_cfg, "[%S]+") do
    fields[item] = read_config(item) or ('you must initialize "' .. item .. '" option')
end

function process_message()
    local data = {}
    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then -- exclude bytes
	    data[name] = value
	end
    end

    for key, value in pairs(fields) do
	data[key] = value
    end

    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Fields = data
    })

    return 0
end
