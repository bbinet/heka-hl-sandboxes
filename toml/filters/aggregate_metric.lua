require "circular_buffer"

local agg = read_config('aggregation') or error('you must initialize "aggregation" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local data = { }

if not agg == ("avg" or "max" or "min" or "sum" or "last") then
    error('"' .. agg .. '" unknow aggregation method: allowed values for aggregation are "avg", "sum", "max", "min", "last"')
end

function process_message()
    local name = read_message('Fields[name]')
    local value = read_message('Fields[value]')

    if data[name] == nil then
	if agg == "avg" then
	    data[name] = { }
	    data[name][#data[name]+1] = value
	else
	    data[name] = value
	end
	return 0
    end

    if agg == "last" then
	data[name] = value
    elseif agg == 'max' then
	if value > data[name] then
	    data[name] = value
	end
    elseif agg == 'min' then
	if value < data[name] then
	    data[name] = value
	end
    elseif agg == 'sum' then
	data[name] = data[name] + value
    else
	data[name][#data[name]+1] = value
    end

    return 0
end

function timer_event(ns)
    for name, cb in pairs(data) do
	local value = 0
	if agg == "avg" then
	    for key in pairs(data[name]) do
		value = value + tonumber(data[name][key])
	    end
	    value = value/(#data[name])
	else
	    value = cb
	end
	inject_message({
	    Type = type_output,
	    Timestamp = ns,
	    Fields = {
		value = value,
		name = name
	    }
	})
    end
    data = { }
end
