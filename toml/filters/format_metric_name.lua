local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local data = {
	Type = type_output,
	Payload = read_message('Payload'),
	Fields = {
	    timestamp = read_message('Timestamp') / 1e9
	}
    }
    local name = read_message('Fields[uuid]') .. '.' .. read_message('Fields[hostname]') .. '.' .. read_message('Fields[name]')
    data.Fields[name] = read_message('Fields[value]')

    inject_message(data)

    return 0
end
