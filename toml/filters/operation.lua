require "circular_buffer"

local agg = read_config('aggregation') or error('you must initialize "aggregation" option')
local sec_per_row = read_config('sec_per_row')
local nb_rows = read_config('nb_rows')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local nb_columns = 1
local cbufs = { }

if agg ~= ("avg" or "sum" or "max" or "min" or "last") then
    error('you must initialize "aggregation" option')
end
if agg ~= last then
    if (sec_per_row) == nil then
	error('you must initialize "sec_per_row" option')
    end
    if (nb_rows) == nil then
	error('you must initialize "nb_rows" option')
    end
end

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

    if agg ~= "last" then
	local cb = cbufs[name]
	if not cb then cb = init_cbuf(name) end
	cb:set(ts, 1, value)
    else
	cbufs[name] = {
	    Type = type_output,
	    Payload = read_message('Payload'),
	    Fields = {
		name = name,
		value = value
	    }
	}
    end

    return 0
end

function timer_event(ns)
    for key, cb in pairs(cbufs) do
	if agg ~= "last" then
	    local value = cb:compute(agg, 1)
	    local data = {
		Type = type_output,
		Timestamp = ns,
		Payload = ns .. ':' .. key .. ':' .. value,
		Fields = {
		    value = value,
		    name  = key
		}
	    }
	    inject_message(data)
	    data = { }
	else
	    cb.Timestamp = ns
	    inject_message(cb)
	    cb = { }
	end
    end
end
