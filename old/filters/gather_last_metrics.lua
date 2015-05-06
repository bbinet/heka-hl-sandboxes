local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = {}

function process_message()
    local name = read_message('Fields[name]')
    if name == nil then
	return -1, "Fields['name'] can't be nil"
    end
    local value = read_message('Fields[value]')
    if value == nil then
	return -1, "Fields['value'] can't be nil"
    end

    fields[name] = value

    return 0
end

function timer_event(ns)
    inject_message({
	Type = type_output,
	Timestamp = ns,
	Fields = fields
    })
    fields = {}
end
