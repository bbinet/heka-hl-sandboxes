local data = {
    Type = 'trwebclient',
    Fields = { }
}

function process_message()
    data.Fields.name = read_message('Fields[name]')
    data.Fields.value = read_message('Fields[value]')
    if read_config('emit_in_payload') then
	data.Payload = data.Fields.name .. ':' .. data.Fields.value
    end
    return 0
end

function timer_event(ns)
    inject_message(data)

    data.Fields = { }
end
