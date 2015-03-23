require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local method = read_config('type_output_method') or 'overwrite'
local trackers_mode = {}

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
end

function process_message()
    local fields = {}
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

    local type_out = type_output
    if method == 'prefix' then
	type_out = type_output .. string.gsub(read_message('Type'), "^heka.sandbox.", "")
    elseif method == 'suffix' then
	type_out = string.gsub(read_message('Type'), "^heka.sandbox.", "") .. type_output
    end

    inject_message({
	Type = type_out,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Severity = read_message('Severity'),
	Fields = fields
    })
    return 0
end
