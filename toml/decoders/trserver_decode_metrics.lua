require "string"
local type_output = read_config('type_output')
if type_output == nil then
    return 1
end

function process_message()
    local data = {
        Type    = type_output,
        Fields  = { }
    }

    data.Fields.name, data.Fields.value = string.match(read_message('Payload'), "^([%w_]+):([%w_.+-]+)|p$")

    data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value

    inject_message(data)

    return 0
end
