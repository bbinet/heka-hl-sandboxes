require "string"
require "cjson"

local version = 0
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local method = read_config('type_output_method') or 'overwrite'

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
end

function process_message()
    local msg = read_message('Fields[msg]')
    if msg == nil then
	return -1, "msg can't be nil"
    end
    
    local fields = {
	encoder_type = "event",
	encoder_version = version
    }
    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    local type_out = type_output
    if method == 'prefix' then
	type_out = type_output .. string.gsub(read_message('Type'), "^heka.sandbox.", "")
    elseif method == 'suffix' then
	type_out = string.gsub(read_message('Type'), "^heka.sandbox.", "") .. type_output
    end

    inject_message({
	Type = type_out,
	Payload = cjson.encode(msg),
	Timestamp = read_message('Timestamp'),
	Severity = read_message('Severity'),
	Fields = fields
    })
    return 0
end
