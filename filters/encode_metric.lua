local version = 0
local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local fields = {
	encoder_type = "metric",
	encoder_version = version
    }

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    if fields['name'] == nil then
	return -1, "Fields['name'] can't be nil"
    end
    if fields['value'] == nil then
	return -1, "Fields['value'] can't be nil"
    end

    inject_message({
	Type = type_output,
	Payload = fields['name'] .. ' ' .. fields['value'],
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })
    return 0
end
