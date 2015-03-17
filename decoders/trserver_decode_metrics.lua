require "string"
local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local payload = read_message('Payload')
    local name, value = string.match(payload, "^([%w_]+):([%w_.+-]+)|p\n$")
    value = tonumber(value)

    if name ~= nil and value ~= nil then
        inject_message({
            Type = type_output,
            Payload = payload,
            Fields = {
                name = name,
                value = value
            }
        })
    end

    return 0
end
