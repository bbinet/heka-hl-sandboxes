require "cjson"
require "string"

local allowed_headers = read_config('allowed_headers')
local headers = {
    'Uuid',
    'Type',
    'Logger',
    'Payload',
    'EnvVersion',
    'Hostname',
    'Timestamp',
    'Severity',
    'Pid',
    'Fields'
}
if allowed_headers ~= nil then
    headers = {}
    for header in string.gmatch(allowed_headers, "[%S]+") do
        headers[#headers+1] = header
    end
end

function process_message()
    local message = {}
    for i, header in ipairs(headers) do
        if header == "Fields" then
            message['Fields'] = {}
            while true do
                typ, name, value = read_next_field()
                if not typ then break end
                if typ ~= 1 then --exclude bytes
                    message['Fields'][name] = value
                end
            end
        else
            message[header] = read_message(header)
        end
    end
    inject_payload("json", "encode_json", cjson.encode(message))

    return 0
end
