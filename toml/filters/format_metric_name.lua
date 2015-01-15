require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = read_config('fields') or error('you must initialize "fields" option')
local splitter = read_config('splitter') or error('you must initialize "splitter" option')

function process_message()
    local name = ""
    for value in string.gmatch(fields, "[%S]+") do
	if read_message('Fields[' .. value .. ']') == nil then
	    error('the Fields: ' .. value .. ' can\' be a nil value')
	end
	if name == "" then
	    name = read_message('Fields[' .. value .. ']')
	else
	    name = name .. splitter .. read_message('Fields[' .. value .. ']')
	end
    end

    local data = {
	Type = type_output,
	Payload = read_message('Payload'),
	Fields = {
	    timestamp = read_message('Timestamp') / 1e9
	}
    }
    data.Fields[name] = read_message('Fields[value]')

    inject_message(data)

    return 0
end
