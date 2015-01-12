require "cjson"

function process_message()
    local payload = { }
    local name = read_message('Fields[name]')
    payload[name] = {
        value = read_message('Fields[value]'),
    }

    inject_payload("json", "server_db", cjson.encode(payload))

    return 0
end
