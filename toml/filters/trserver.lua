require "string"

local uuid = read_config('uuid') or 'message_not_parse'

function process_message()
    local data = {
        Type    = 'heka.statmetric.decoder',
        Payload = nil,
        Fields  = { }
    }

    local payload = read_message("Payload")
    local position = 'parseName'
    for token in string.gmatch(payload, "([^{:,|}]+)") do
	if position == 'parseValue' then
	    data.Fields.value = tonumber(token)
	    break
	end
	if position == 'parseName' then
	    data.Fields.name = uuid .. '.' .. token
	    position = 'parseValue'
	end
    end

    data.Payload = read_message('Timestamp') .. ':' .. data.Fields.name .. ':' .. data.Fields.value
    inject_message(data)
    data = { }

    return 0
end
