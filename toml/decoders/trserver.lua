require "string"

local uuid = read_config('uuid') or 'uuid_not_parse'
local hostname = read_config('hostname') or 'masterControllerName_not_parse'

function process_message()
    local type_output = read_config('type_output') or nil

    if type_output then
        type_output = 'heka.statmetric.' .. type_output
    else
	type_output = 'heka.statmetric'
    end

    local data = {
        Type    = type_output,
        Payload = nil,
        Fields  = {
	    uuid = uuid,
	    hostname = hostname
	}
    }

    local payload = read_message("Payload") .. ''
    data.Fields.name, data.Fields.value = string.match(payload, "^([%w_]+):([%w_.+]+)|p$")

    data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value
    inject_message(data)
    data = { }

    return 0
end
