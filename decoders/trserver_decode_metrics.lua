require "string"
local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local name, value = string.match(read_message('Payload'), "^([%w_]+):([%w_.+-]+)|p\n$")
    value = tonumber(value)
    if name == nil then
	return -1, "name can't be nil"
    end
    if value == nil then
	return -1, "value can't be nil"
    end

    if name ~= nil and value ~= nil then
        inject_message({
            Type = type_output,
            Fields = {
                name = name,
                value = value
            }
        })
    end

    return 0
end
