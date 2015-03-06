require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local regex = table.concat({
    "^%[(%d%d:%d%d:%d%d)", --time
    "([%w-]+)",            --hostname
    "(%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x)",--uuid
    "(%d+)",               --epoch time
    "(%l+):(%d+)%]",       --log_type and log_version
    "(.*)\n$"              --log
}, ' ')

function process_message()
    local time, hostname, uuid, timestamp, typ, version, payload =
        string.match(read_message('Payload'), regex)
    if typ ~= "metric" and typ ~= "event" then
        return -1, "unknown type: supported types are one of: [metric|event]"
    end

    inject_message({
        Type = type_output,
        Timestamp = timestamp,
        Payload = payload,
        Fields = {
            uuid = uuid,
            hostname = hostname,
            decoder_type = typ,
            decoder_version = tonumber(version)
        }
    })

    return 0
end
