require "string"

local agg = read_config('aggregation') or error('you must initialize "aggregation" option')
if  agg ~= "avg" and agg ~= "max" and agg ~= "min" and agg ~= "sum" and agg ~= "last" and agg ~= "count" and agg ~= "no" then
    error('"' .. agg .. '" unknown aggregation method: allowed values for aggregation are "avg", "sum", "max", "min", "last", "count", "no"')
end
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local ticker_interval = read_config('ticker_interval') or error('you must initialize "ticker_interval" option')
local gust = read_config('gust')
local gusts = nil
local gust_ns = nil
if gust ~= nil then
    if type(gust) ~= "number" then
	error('if gust is set, it must be a number')
    end
    gusts = {}
    gust_ns = gust * 10^9
end
local data = {}

function process_message()
    local ts = read_message('Timestamp')
    local name = read_message('Fields[name]')
    local value = tonumber(read_message('Fields[value]'))
    if name == nil then
	return -1, "Fields[name] cant be nil"
    end
    if value == nil then
	return -1, "Fields[value] cant be nil"
    end
    if agg == "no" then
	local msg = {
	    Type = type_output,
	    Timestamp = ts,
	    Severity = 7,
	    Fields = {
		_agg = agg
	    }
	}
	msg['Fields'][name] = value
	inject_message(msg)
    end

    if gust ~= nil then
	gusts[name] = {
	    t = ts,
	    value = value,
	    next = gusts[name]
	}
	local count = 0
	local sum = 0
	local l = gusts[name]
	while l do
	    count = count + 1
	    sum = sum + l.value
	    if l.next ~= nil and l.next.t < ts - gust_ns then
		l.next = nil
	    end
	    l = l.next
	end
	-- override value with the average of the gust
	value = sum / count
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
    if agg == "no" then
	return 0
    end
    local msg = {
	Type = type_output,
	Timestamp = ns,
	Severity = 7,
	Fields = {
	    _tick = ticker_interval,
	    _agg = agg
	}
    }
    if gust ~= nil then
	msg['Fields']['_gust'] = gust
    end
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
    data = {}
end
