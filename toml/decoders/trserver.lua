require "string"

function process_message()
    local type_output = read_config('type_output') or nil

    if type_output then
        type_output = 'heka.statmetric.' .. type_output
    else
	type_output = 'heka.statmetric'
    end

    local data = {
        Type    = type_output,
        Fields  = { }
    }

    local payload = read_message("Payload") .. ''
    data.Fields.name, data.Fields.value = string.match(payload, "^([%w_]+):([%w_.+-]+)|p$")

    if read_config('emit_in_payload') then
        data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value
    end
    inject_message(data)
    data = { }

    return 0
end
