require "string"
require "table"

function process_message()
    local timestamp = read_message('Timestamp')
    local hostname = read_message('Fields[hostname]')
    local uuid = read_message('Fields[uuid]')
    local name = read_message('Fields[name]')
    local value = read_message('Fields[value]')

    if timestamp == nil then
        return -1, "Timestamp can't be nil"
    end
    if hostname == nil then
        return -1, "Fields[hostname] can't be nil"
    end
    if uuid == nil then
        return -1, "Fields[uuid] can't be nil"
    end
    if name == nil then
        return -1, "Fields[name] can't be nil"
    end
    if value == nil then
        return -1, "Fields[value] can't be nil"
    end

    local path = table.concat({uuid, hostname, name}, ".")

    inject_payload('txt', 'encode_carbon', table.concat({
        path,
        value,
        string.format("%d", timestamp/1e9),
    }, " ") .. '\n')

    return 0
end
