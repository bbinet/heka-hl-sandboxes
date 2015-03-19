require "string"
require "table"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local regex = table.concat({
    "^%[(%d%d:%d%d:%d%d)", -- time
    "([%w-]+)",            -- hostname
    "(%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x)", -- uuid
    "(%d+)",               -- epoch formatted time
    "([0-7])",             -- severity
    "(%l+):(%d+)%]",       -- decoder_type:decoder_version
    "(.*)\n$"              -- custom part (to forward to a specialized decoder)
}, ' ')

function process_message()
    local time, hostname, uuid, timestamp, severity, typ, version, payload =
        string.match(read_message('Payload'), regex)
    -- if regex don't match, every variables above will be set to nil
    -- so we don't need to check all variables, only one is sufficient
    if timestamp == nil then
        return -1, "regex doesn't match"
    end
    if typ ~= "metric" and typ ~= "event" then
        return -1, "unknown type: supported types are one of: [metric|event]"
    end

    inject_message({
        Type = type_output,
        Timestamp = timestamp,
        Payload = payload,
        Severity = severity,
        Fields = {
            uuid = uuid,
            hostname = hostname,
            decoder_type = typ,
            decoder_version = tonumber(version)
        }
    })

    return 0
end
