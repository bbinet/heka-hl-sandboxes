require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local regex = { }
regex[#regex+1] = "^%[(%d%d:%d%d:%d%d)" --time
regex[#regex+1] = "([%w-]+)"            --hostname
regex[#regex+1] = "(%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x)"--uuid
regex[#regex+1] = "(%d+)"               --epoch time
regex[#regex+1] = "(%l+):(%d+)%]"       --log_type and log_version
regex[#regex+1] = "(.*)$"               --log

function process_message()
    local payload = read_message('Payload')
    local time, hostname, uuid, timestamp, typ, version, log = string.match(payload, table.concat(regex, ' '))

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
