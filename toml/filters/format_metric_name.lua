require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = read_config('fields') or error('you must initialize "fields" option')
local separator = read_config('separator') or error('you must initialize "separator" option')

function process_message()
    local parts = { }
    for part in string.gmatch(fields, "[%S]+") do
	if read_message('Fields[' .. part .. ']') == nil then
	    --error('the Fields: ' .. part .. ' can\' be a nil value')
	end
	parts[#parts+1] = read_message('Fields[' .. part .. ']')
    end

    local new_name = table.concat(parts, separator)
    local data = {
	Type = type_output,
	Payload = read_message('Payload'),
	Fields = {
	    timestamp = read_message('Timestamp') / 1e9
	}
    }
    data.Fields[new_name] = read_message('Fields[value]')

    inject_message(data)

    return 0
end
