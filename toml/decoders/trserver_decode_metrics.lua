require "string"
local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local data = {
        Type = type_output,
        Payload = read_message('Payload'),
        Fields = { }
    }

    data.Fields.name, data.Fields.value = string.match(data.Payload, "^([%w_]+):([%w_.+-]+)|p$")


    inject_message(data)

    return 0
end
