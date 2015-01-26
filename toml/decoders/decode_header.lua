require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local regex = { }
regex[#regex+1] = "^%[(%d%d:%d%d:%d%d)" --time
regex[#regex+1] = "(%d%.%d+e%+%d+)"     --epoch time
regex[#regex+1] = "(%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x)"--uuid
regex[#regex+1] = "([%w-]+)"            --hostname
regex[#regex+1] = "(.+):(%d+)%](.*)$"   --log_type, log_version and log

function process_message()
    local payload = read_message('Payload')
    local time, date, uuid, hostname, log_type, log_version, log = string.match(payload, table.concat(regex, '%s'))

    if log_type ~= "metric" and log_type ~= "event" and log_type ~= "alert" then
        return 0 --TODO: print error message
    end

    inject_message({
        Type = type_output .. '.' .. log_type .. '.' .. log_version,
        Timestamp = date,
        Payload = log,
        Fields = {
            uuid = uuid,
            hostname = hostname
        }
    })

    return 0
end
