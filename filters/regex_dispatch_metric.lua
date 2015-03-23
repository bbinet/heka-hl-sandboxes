require "string"

local matcher = read_config('matchers') or error ('you must initialize "matchers" option')
local method = read_config('type_output_method') or 'overwrite'
local matchers = {}

for value in string.gmatch(matcher, "[%S]+") do
    matchers[#matchers + 1] = {
	type_output = read_config(value .. '_type_output') or error ('you must initialize "' .. value .. '_type_output" option'),
	regex = read_config(value .. '_regex') or error ('you must initialize "' .. value .. '_regex" option')
    }
end

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
end

function process_message()
    local fields = {}
    while true do
	typ, key, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[key] = value
	end
    end

    for index, item in ipairs(matchers) do
	if string.find(read_message('Fields[name]'), "^" .. item.regex .. "$") ~= nil then
	    local type_out = item.type_output
	    if method == 'prefix' then
		type_out = item.type_output .. string.gsub(read_message('Type'), "^heka.sandbox.", "")
	    elseif method == 'suffix' then
		type_out = string.gsub(read_message('Type'), "^heka.sandbox.", "") .. item.type_output
	    end

	    inject_message({
		Type = type_out,
		Timestamp = read_message('Timestamp'),
		Payload = read_message('Payload'),
		Severity = read_message('Severity'),
		Fields = fields
	    })
	    break
	end
    end

    return 0
end
