require "cjson"
require "string"

local type_output = read_config('type_output')
local allowed_headers = read_config('allowed_headers')
local headers = nil
if allowed_headers ~= nil then
    headers = {}
    for header in string.gmatch(allowed_headers, "[%S]+") do
        headers[#headers+1] = header
    end
end

function process_message()
    local data = cjson.decode(read_message('Payload'))
    if type(data) ~= "table" then
        return -1, "invalid json"
    end

    message = data
    if headers ~= nil then
        message = {}
        for i, header in ipairs(headers) do
            message[header] = data[header]
        end
    end

    if type_output ~= nil then
        message["Type"] = type_output
    end

    inject_message(message)

    return 0
end
