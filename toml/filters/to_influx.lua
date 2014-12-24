function process_message()
    local data = {
	Payload = read_message('Payload'),
	Type = 'influx',
	Fields = {
	    timestamp = read_message('Timestamp') / 1e9
	}
    }
    local name = read_message('Fields[name]')
    data.Fields[name] = read_message('Fields[value]')

    inject_message(data)

    return 0
end
