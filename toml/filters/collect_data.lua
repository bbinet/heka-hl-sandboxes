require "cjson"

local data = {
    Type = 'trwebclient',
    Payload = nil
}
local message = { }

function process_message()
    local name = read_message('Fields[name]')
    message[name] = {
        value = read_message('Fields[value]'),
        time  = read_message('Timestamp') / 1e9
    }

    return 0
end

function timer_event(ns)
    data.Payload = cjson.encode(message)
    inject_message(data)

    message = { }
end
