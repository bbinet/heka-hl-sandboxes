require "cjson"

function process_message()
    local fields = { }
    while true do
        typ, name, value = read_next_field()
        if not typ then break end
        if typ ~= 1 then --exclude bytes
            fields[name] = value
        end
    end
    inject_payload("json", "testEncoder", cjson.encode({
        Timestamp = read_message('Timestamp'),
        Type = read_message('Type'),
        Severity = read_message('Severity'),
        Logger = read_message('Logger'),
        Payload = read_message('Payload'),
        Fields = fields
    }))

    return 0
end
