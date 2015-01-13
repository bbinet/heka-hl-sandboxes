require "circular_buffer"

local agg = read_config('aggregation')
local sec_per_row = read_config('sec_per_row')
local nb_rows = read_config('nb_rows')
local type_output = read_config('type_output')
local nb_columns = 1
local cbufs = { }

function init()
    if agg ~= ("avg" or "sum" or "max" or "min" or "last") then
	return 1
    end
    if agg ~= last then
	if (sec_per_row or nb_rows) == nil then
	    return 1
	end
    end
    if type_output == nil then
	return 1
    end
end
init()

function init_cbuf(name)
    cb = circular_buffer.new(nb_rows, nb_columns, sec_per_row)
    cb:set_header(1, name, 'count', 'none')
    cbufs[name] = cb

    return cb
end

function process_message()
    local ts    = read_message('Timestamp')
    local name  = read_message('Fields[name]')
    local value = read_message('Fields[value]')

    local cb = cbufs[name]
    if not cb then cb = init_cbuf(name) end
    cb:set(ts, 1, value)

    return 0
end

function timer_event(ns)
    local emit_in_payload = read_config('emit_in_payload')
    for key, cb in pairs(cbufs) do
	local value = cb:compute(agg, 1)
        local data = {
	    Type = type_output,
	    Timestamp = ns,
	    Fields = {
		value = value,
		name  = key
	    }
        }
	if emit_in_payload then
	    Payload = ns .. ':' .. key .. ':' .. value
	end
	inject_message(data)
	data = { }
    end
end
