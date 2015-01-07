require "cjson"

function process_message()
    local name = read_message('Fields[name]')
    local data = { }
    data[name] = {
        value = read_message('Fields[value]'),
        time  = read_message('Timestamp')
    }

    inject_payload("json", "server_db", cjson.encode(data))

    return 0
end
