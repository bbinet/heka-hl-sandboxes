require "string"

local matchers = read_config('matchers')
local data = {
    Fields = { }
}

for value in string.gmatch(matchers, "[%S]+") do
    data.Fields[value] = read_config(value)
end

function process_message()
    if read_config('emit_in_payload') then
	data.Payload = read_message('Payload')
    end

    data.Type = read_config('type_output')
    data.Timestamp = read_message('Timestamp')
    data.Fields.name = read_message('Fields[name]')
    data.Fields.value = read_message('Fields[value]')

    inject_message(data)

    return 0
end
