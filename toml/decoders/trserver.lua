require "string"

local uuid = read_config('uuid') or 'uuid_not_parse'
local masterController = read_config('masterController') or 'masterControllerName_not_parse'

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
	    masterController = masterController
	}
    }

    local payload = read_message("Payload")
    local position = 'parseName'
    for token in string.gmatch(payload, "([^{:,|}]+)") do
	if position == 'parseValue' then
	    data.Fields.value = tonumber(token)
	    break
	end
	if position == 'parseName' then
	    data.Fields.name = token
	    position = 'parseValue'
	end
    end

    data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value
    inject_message(data)
    data = { }

    return 0
end
