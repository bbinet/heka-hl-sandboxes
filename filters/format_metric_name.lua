require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local method = read_config('type_output_method') or 'overwrite'
local fields_str = read_config('fields') or error('you must initialize "fields" option')
local separator = read_config('separator') or error('you must initialize "separator" option')
local fields = {}
for field in string.gmatch(fields_str, "[%S]+") do
    fields[#fields+1] = field
end

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
end

function process_message()
    local parts = { }
    for i, field in ipairs(fields) do
	part = read_message('Fields[' .. field .. ']')
	if part == nil then
	    return -1, "'Fields[" .. field .. "]' can't be nil"
	end
	parts[#parts+1] = part
    end

    local f = {}
    while true do
	typ, key, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    f[key] = value
	end
    end
    f['name'] = table.concat(parts, separator)

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
	Fields = f
    })

    return 0
end
