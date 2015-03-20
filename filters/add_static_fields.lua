require "string"

local fields_cfg = read_config('fields') or error('you must initialize "fields" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local method = read_config('type_output_method') or 'overwrite'
local fields = { }
for item in string.gmatch(fields_cfg, "[%S]+") do
    fields[item] = read_config(item) or ('you must initialize "' .. item .. '" option')
end

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
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

    local type_out = type_output
    if method == 'prefix' then
	type_out = type_output .. read_message('Type')
    elseif method == 'suffix' then
	type_out = read_message('Type') .. type_output
    end

    inject_message({
	Type = type_out,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Severity = read_message('Severity'),
	Fields = data
    })

    return 0
end
