local type_output = read_config('type_output')
if type_output == nil then
    return 1
end
local data = {
    Type = type_output,
    Timestamp = read_message('Timestamp'),
    Fields = { }
}

function process_message()
    data.Fields[read_message('Fields[name]')] = read_message('Fields[value]')

    return 0
end

function timer_event(ns)
    inject_message(data)
end
