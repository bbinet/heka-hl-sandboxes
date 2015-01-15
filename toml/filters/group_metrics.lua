local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local fields = {
}

function process_message()
    fields[read_message('Fields[name]')] = read_message('Fields[value]')

    return 0
end

function timer_event(ns)
    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })
    fields = { }
end
