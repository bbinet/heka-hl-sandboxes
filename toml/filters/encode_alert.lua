local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local alert_version = 0

function process_message()
    local message = read_message('Fields[message]')
    local level = read_message('Fields[level]')
    local fields = {
	type = "alert",
	encoder_version = alert_version,
	log = '[' .. message .. ' ' .. level .. ']'
    }

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    inject_message({
	Type = type_output,
	Payload = read_message('Payload'),
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })
    return 0
end
