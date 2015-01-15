require "string"

local fields = read_config('fields') or error('you must initialize "fields" option')
local data = {
    Fields = { }
}

for value in string.gmatch(fields, "[%S]+") do
    data.Fields[value] = read_config(value)
end

function process_message()
    data.Type = read_config('type_output')
    if data.Type == nil then
	return 1
    end
    data.Timestamp = read_message('Timestamp')
    local message = "|"
    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then -- exclude bytes
	    data.Fields[name] = value
	    message = message .. value .. ':'
	end
    end

    if read_config('emit_in_payload') then
	data.Payload = data.Timestamp .. ':' .. data.Fields.name .. ':' .. data.Fields.value .. message
    end
    inject_message(data)

    return 0
end
