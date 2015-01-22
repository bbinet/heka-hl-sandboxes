require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local emit_timestamp_in_sec = read_config('emit_timestamp_in_sec') or false
local fields = read_config('fields') or error('you must initialize "fields" option')
local separator = read_config('separator') or error('you must initialize "separator" option')
local timestamp = 1


if emit_timestamp_in_sec == true then
    timestamp = 1e9
elseif emit_timestamp_in_sec ~= false then
    error('you must initialize "emit_timestamp_in_sec" option: allowed value "true", default: "false"')
end

function process_message()
    local parts = { }
    for part in string.gmatch(fields, "[%S]+") do
	if read_message('Fields[' .. part .. ']') == nil then
	    return 0 --TODO: echo "the Fields: " .. part .. " can't be a nil value"
	end
	parts[#parts+1] = read_message('Fields[' .. part .. ']')
    end

    local data = {
	Type = type_output,
	Payload = read_message('Payload'),
	Fields = {
	    timestamp = read_message('Timestamp') / timestamp
	}
    }
    data.Fields[table.concat(parts, separator)] = read_message('Fields[value]')

    inject_message(data)

    return 0
end
