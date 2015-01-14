require "string"

function process_message()
    local type_output = read_config('type_output')

    if type_output == nil then
        return 1
    end

    local data = {
        Type    = type_output,
        Fields  = { }
    }

    local payload = read_message("Payload") .. ''
    data.Fields.name, data.Fields.value = string.match(payload, "^([%w_]+):([%w_.+-]+)|p$")

    data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value

    inject_message(data)
    data = { }

    return 0
end
