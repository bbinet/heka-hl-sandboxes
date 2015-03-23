require "string"

local aggregation = read_config('aggregation') or error('you must initialize "aggregation" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
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
    for index, agg in pairs(aggs) do
	for name, cb in pairs(data) do
	    local value = 0
	    if agg == "avg" then
		value = data[name].sum/data[name].count
	    else
		value = data[name][agg]
	    end
	    inject_message({
		Type = type_output,
		Timestamp = ns,
		Severity = 7,
		Fields = {
		    aggregation = agg,
		    value = value,
		    name = name
		}
	    })
	end
    end
    data = {}
end
