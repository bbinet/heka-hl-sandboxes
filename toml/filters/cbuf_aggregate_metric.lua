require "circular_buffer"

local agg = read_config('aggregation') or error('you must initialize "aggregation" option')
local sec_per_row = read_config('sec_per_row')
local nb_rows = read_config('nb_rows')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local nb_columns = 1
local cbufs = { }

if not agg == ("avg" or "max" or "min" or "sum" or "last") then
    error('"' .. agg .. '" unknow aggregation method: allowed values for aggregation are "avg", "sum", "max", "min", "last"')
end
if not agg == last and sec_per_row == nil then
    error('you must initialize "sec_per_row" option')
end
if not agg == last and nb_rows == nil then
    error('you must initialize "nb_rows" option')
end

function init_cbuf(name)
    cb = circular_buffer.new(nb_rows, nb_columns, sec_per_row)
    cb:set_header(1, name, 'count', 'none')
    cbufs[name] = cb

    return cb
end

function process_message()
    local ts = read_message('Timestamp')
    local name = read_message('Fields[name]')
    local value = read_message('Fields[value]')

    if agg ~= "last" then
	local cb = cbufs[name]
	if not cb then cb = init_cbuf(name) end
	cb:set(ts, 1, value)
    else
	cbufs[name] = value
    end

    return 0
end

function timer_event(ns)
    for key, cb in pairs(cbufs) do
	local value = nil
	if agg ~= "last" then
	    value = cb:compute(agg, 1)
	else
	    value = cb
	end
	inject_message({
	    Type = type_output,
	    Timestamp = ns,
	    Fields = {
		value = value,
		name = key
	    }
	})
    end
end
