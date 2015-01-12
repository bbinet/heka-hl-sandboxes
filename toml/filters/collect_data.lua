local data = {
    Type = 'trwebclient',
    Payload = nil,
    Fields = { }
}

function process_message()
    data.Fields.name = read_message('Fields[name]')
    data.Fields.value = read_message('Fields[value]')
    data.Payload = data.Fields.name .. ':' .. data.Fields.value

    return 0
end

function timer_event(ns)
    inject_message(data)

    data.Fields = { }
end
