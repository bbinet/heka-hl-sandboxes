require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local regex = table.concat({
    "^%[(%d%d:%d%d:%d%d)", --time
    "([%w-]+)",            --hostname
    "(%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x)",--uuid
    "(%d+)",               --epoch time
    "(%l+):(%d+)%]",       --log_type and log_version
    "(.*)$"               --log
}, ' ')

function process_message()
    local payload = read_message('Payload')
    local time, hostname, uuid, timestamp, typ, version, log = string.match(payload, regex)

    if typ ~= "metric" and typ ~= "event" and typ ~= "alert" then
        return 0 --TODO: print error message
    end

    inject_message({
        Type = type_output,
        Timestamp = timestamp,
        Payload = log,
        Fields = {
            uuid = uuid,
            hostname = hostname,
            type = typ,
            version = version
        }
    })

    return 0
end
