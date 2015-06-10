require "string"
require "table"
require "os"

function process_message()
    local timestamp = read_message('Timestamp')
    local hostname = read_message('Fields[hostname]')
    local uuid = read_message('Fields[uuid]')
    local severity = read_message("Severity")
    local encoder_type = read_message('Fields[encoder_type]')
    local encoder_version = read_message('Fields[encoder_version]')
    local payload = read_message('Payload')

    if timestamp == nil then
        return -1, "Timestamp can't be nil"
    end
    if hostname == nil then
        return -1, "Fields[hostname] can't be nil"
    end
    if uuid == nil then
        return -1, "Fields[uuid] can't be nil"
    end
    if severity == nil then
        return -1, "Severity can't be nil"
    end
    if encoder_type == nil then
        return -1, "Fields[encoder_type] can't be nil"
    end
    if encoder_version == nil then
        return -1, "Fields[encoder_version] can't be nil"
    end
    if payload == nil then
        return -1, "Payload can't be nil"
    end

    inject_payload('txt', 'encode_header', '[' .. table.concat({
        os.date("%X", timestamp/1e9),
        hostname,
        uuid,
        -- workaround for lua5.1 on arch arm
        string.format("%.0f", timestamp),
        severity,
        encoder_type .. ':' .. encoder_version
    }, " ") .. '] ' .. payload .. '\n')

    return 0
end
