function process_message()
    local data = {
	Type = 'influx',
	Fields = {
	    timestamp = read_message('Timestamp') / 1e9
	}
    }
    local name = read_message('Fields[uuid]') .. '.' .. read_message('Fields[hostname]') .. '.' .. read_message('Fields[name]')
    data.Fields[name] = read_message('Fields[value]')

    if read_config('emit_in_payload') then
	data.Payload = data.Fields.timestamp .. ':' .. name .. ':' .. data.Fields[name]
    end
    inject_message(data)

    return 0
end
