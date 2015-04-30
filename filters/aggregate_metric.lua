require "string"

local aggregation = read_config('aggregation') or error('you must initialize "aggregation" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local ticker_interval = read_config('ticker_interval') or error('you must initialize "ticker_interval" option')
local data = {}
local aggs = {}

for agg in string.gmatch(aggregation, "[%S]+") do
    if  agg ~= "avg" and agg ~= "max" and agg ~= "min" and agg ~= "sum" and agg ~= "last" and agg ~= "count" then
	error('"' .. agg .. '" unknown aggregation method: allowed values for aggregation are "avg", "sum", "max", "min", "last", "count"')
    end
    aggs[agg] = agg
end

function process_message()
    local name = read_message('Fields[name]')
    local value = tonumber(read_message('Fields[value]'))
    if name == nil then
	return -1, "Fields[name] cant be nil"
    end
    if value == nil then
	return -1, "Fields[value] cant be nil"
    end

    if data[name] == nil then
	data[name] = {
	    last = value,
	    min = value,
	    max = value,
	    sum = value,
	    count = 1
	}
	return 0
    end
    
    data[name].last = value
    if value < data[name].min then data[name].min = value end
    if value > data[name].max then data[name].max = value end
    data[name].sum = data[name].sum + value
    data[name].count = data[name].count + 1
    return 0
end

function timer_event(ns)
    local msg = {
	Type = type_output,
	Timestamp = ns,
	Severity = 7,
	Fields = {
	    _ticker_interval = ticker_interval
	}
    }
    for index, agg in pairs(aggs) do
	msg['Fields']['_aggregation'] = agg
	for name, cb in pairs(data) do
	    if agg == 'avg' then
		msg['Fields'][name] = data[name].sum/data[name].count
	    else
		msg['Fields'][name] = data[name][agg]
	    end
	end
	if next(data) ~= nil then
	    inject_message(msg)
	end
    end
    data = {}
end
